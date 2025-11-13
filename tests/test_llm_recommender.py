from src.services.llm_recommender import _extract_json, _build_prompt
from src.models.product import Product


def _make_product(pid, name, description=None, category=None, price=None):
    p = Product()
    p.id = pid
    p.name = name
    p.description = description
    p.category = category
    p.price = price
    return p


def test_extract_json_direct_and_wrapped():
    arr = '[{"product_id": "1", "score": 1.0}]'
    # direct
    assert _extract_json(arr) == arr

    # wrapped with text
    wrapped = "Here is some text\n" + arr + "\nand tail"
    extracted = _extract_json(wrapped)
    assert extracted is not None
    assert extracted.strip() == arr


def test_build_prompt_contains_target_and_candidates():
    target = _make_product("t1", "Target product", "A product", "CatA", 100)
    c1 = _make_product("c1", "Candidate One", "desc1", "CatA", 90)
    c2 = _make_product("c2", "Candidate Two", "desc2", "CatA", 110)

    prompt = _build_prompt(target, [c1, c2], top_k=2)

    # basic sanity checks
    assert "id: t1" in prompt
    assert "Candidate One" in prompt
    assert "Candidate Two" in prompt
    assert "Réponds au format JSON" in prompt
