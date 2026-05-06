# tests/test_migrate.py
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.migrate import extract_js_object, transform_blocks, transform_profiles

HTML_SNIPPET = """
const PROFILES = {
  engineer: { color:'#0072B8', title:'QA Engineer', accent:'Engineer', sub:'Technisch.' }
};
const BLOCKS = {
  engineer: [
    { section:'QA Engineering', badge:'Fundament', items:[
      { id:'qa2-cloud', name:'Introductie Cloud', icon:'☁️', desc:'Cloud intro.', tags:['Cloud'], dur:'2 sessies', kern:true, cross:['maatwerk'] }
    ]}
  ]
};
"""

def test_transform_profiles():
    raw = {"engineer": {"color": "#0072B8", "title": "QA Engineer", "accent": "Engineer", "sub": "Technisch."}}
    result = transform_profiles(raw)
    assert result["engineer"]["kleur"] == "#0072B8"
    assert result["engineer"]["titel"] == "QA Engineer"
    assert "accent" not in result["engineer"]

def test_transform_blocks_veldnamen():
    raw = {
        "engineer": [
            {"section": "QA Engineering", "badge": "Fundament", "items": [
                {"id": "qa2-cloud", "name": "Cloud", "icon": "☁️", "desc": "desc",
                 "tags": ["Cloud"], "dur": "2 sessies", "kern": True, "cross": ["maatwerk"]}
            ]}
        ]
    }
    result = transform_blocks(raw)
    item = result["engineer"][0]["items"][0]
    assert item["naam"] == "Cloud"
    assert item["duur"] == "2 sessies"
    assert "name" not in item
    assert "dur" not in item

def test_transform_blocks_sectie_badge():
    raw = {
        "engineer": [
            {"section": "QA Engineering", "badge": "Fundament", "items": []}
        ]
    }
    result = transform_blocks(raw)
    assert result["engineer"][0]["sectie"] == "QA Engineering"
    assert "section" not in result["engineer"][0]
