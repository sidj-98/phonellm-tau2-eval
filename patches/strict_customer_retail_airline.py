import os, sys
import tau2.environment.environment as E
NOTE = """

## Calculator
You have a `calculate` tool. Use it only when the arithmetic is hard to do in your head, and call it at most once per sum. When it returns a number, use that number in your next message to the customer. Never call `calculate` again with the same expression: you already have the answer."""
if os.environ.get("AIR_PATCH") == "1":
    _orig = E.Environment.get_policy
    def _gp(self):
        p = _orig(self)
        return p + NOTE if self.domain_name == "airline" else p
    E.Environment.get_policy = _gp
import tau2.user.user_simulator as us
RULE = """

## Additional strict rules for this call (override anything above that suggests otherwise)
- You are a non-technical customer. State your request at the start, then answer only the question the support agent just asked, in one or two short sentences.
- Do not volunteer details, options, or requests the agent has not asked about. Reveal information from your task instructions only when it is asked for or needed to answer.
- Do not make decisions the agent did not ask you to make.
- If you are asked for something you do not know or that is not in your task instructions, say you do not know."""
_o = us.UserSimulator.system_prompt.fget
us.UserSimulator.system_prompt = property(lambda self: _o(self) + RULE)
import tau2.evaluator.evaluator_nl_assertions as _nl
if os.environ.get("NL_JUDGE"):
    _nl.DEFAULT_LLM_NL_ASSERTIONS = os.environ["NL_JUDGE"]
from tau2.cli import main
sys.argv = ["tau2"] + sys.argv[1:]
main()
