import asyncio
from app.agents.skill_extraction_graph import skill_extraction_graph

JD = """
We are looking for a Senior React Developer to join our team.
You must have 5+ years of experience with React and TypeScript.
Redux or Zustand for state management is required.
Experience with Jest and React Testing Library is expected.
AWS knowledge is a plus.
"""

async def main():
    result = await skill_extraction_graph.ainvoke({"jd_text": JD, "position_id": None})
    print("=== SKILLS ===")
    for s in result["skills"]:
        print(f"  {s['skill_name']} | {s['category']} | {s['min_proficiency']} | required={s['is_required']}")
    print(f"\n=== SUMMARY ===\n{result['summary']}")
    print(f"\n=== SENIORITY === {result['suggested_seniority']}")
    print(f"\n=== TRACE ===")
    for entry in result["trace"]:
        print(f"  [{entry['node']}] {entry['duration_ms']}ms — {entry['output_summary']}")

asyncio.run(main())
