"""Native graph execution, including stop and delivery boundaries."""
import pytest
from app.ai.graphs.creative_supervisor import run_creative_supervisor, validate_request


def test_native_graph_stops_at_missing_model():
    result = run_creative_supervisor('A forest explorer.\n\nA new discovery.', ['brief', 'storyboard', 'generate', 'quality', 'delivery'])
    assert result['runtime'] == 'langgraph'
    assert result['status'] == 'blocked'
    assert [t['task'] for t in result['trace']] == ['brief', 'storyboard', 'generate']
    assert len(result['outputs']['storyboard']['shots']) == 2
    assert result['published'] is False


def test_registered_worker_and_gate_reach_review_without_publication():
    result = run_creative_supervisor('Test shot', ['generate', 'quality', 'delivery'], {
        'generate': lambda state: {'artifact': {'asset_id': 'fixture-artifact'}},
        'quality': lambda state: {'passed': True, 'checks': ['fixture check']},
    })
    assert result['status'] == 'awaiting_review'
    assert result['outputs']['delivery']['published'] is False


def test_quality_failure_stops_delivery():
    result = run_creative_supervisor('Test shot', ['generate', 'quality', 'delivery'], {
        'generate': lambda state: {'artifact': {'asset_id': 'fixture-artifact'}},
        'quality': lambda state: {'passed': False},
    })
    assert result['status'] == 'blocked'
    assert 'delivery' not in result['outputs']


@pytest.mark.parametrize('output', [{'simulated': True, 'artifact': 'fake'}, {}, 'not structured'])
def test_invalid_worker_result_fails_closed(output):
    result = run_creative_supervisor('Test shot', ['generate', 'delivery'], {'generate': lambda state: output})
    assert result['status'] == 'failed'
    assert len(result['trace']) == 1
    assert 'delivery' not in result['outputs']


def test_throwing_worker_does_not_advance():
    def fail(state):
        raise RuntimeError('provider secret must not be returned')
    result = run_creative_supervisor('Test shot', ['generate', 'delivery'], {'generate': fail})
    assert result['status'] == 'failed'
    assert 'provider secret' not in str(result)


@pytest.mark.parametrize('objective,tasks', [('', ['brief']), ('x', []), ('x', ['publish']), ('x', ['brief','brief']), ('x', ['delivery','generate']), ('x'*12001, ['brief'])])
def test_invalid_plan_rejected(objective, tasks):
    with pytest.raises(ValueError):
        validate_request(objective, tasks)


@pytest.mark.asyncio
async def test_supervisor_api_requires_authentication(session):
    import httpx
    from app.main import app
    from app.core.database import get_session
    async def override():
        yield session
    app.dependency_overrides[get_session] = override
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/api/v1/agents/supervise', json={'objective': 'A forest story'})
            assert response.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_supervisor_api_saves_owner_scoped_real_trace(engine, test_user_profile, test_auth_token):
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.main import app
    from app.core.database import get_session
    from app.models.ai_generation import AIGeneration
    from app.models.user import User
    async with AsyncSession(engine, expire_on_commit=False) as session:
        owner = User(uid=test_user_profile.uid, email=test_user_profile.email, provider='local', is_active=True)
        session.add(owner)
        await session.commit()
        async def override():
            yield session
        app.dependency_overrides[get_session] = override
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test', headers={'Authorization': 'Bearer '+test_auth_token}) as client:
                response = await client.post('/api/v1/agents/supervise', json={'objective': 'A forest story', 'tasks': ['brief','storyboard','generate','quality','delivery']})
                assert response.status_code == 200, response.text
                result = response.json()
                assert result['runtime'] == 'langgraph' and result['status'] == 'blocked'
                row = await session.get(AIGeneration, result['id'])
                assert row.user_id == owner.id and row.status == 'blocked'
                invalid = await client.post('/api/v1/agents/supervise', json={'objective':'x','tasks':['delivery','generate']})
                assert invalid.status_code == 422
        finally:
            app.dependency_overrides.clear()
