from _Framework.Capabilities import AUTO_LOAD_KEY
from _Framework.Capabilities import CONTROLLER_ID_KEY
from _Framework.Capabilities import NOTES_CC
from _Framework.Capabilities import PORTS_KEY
from _Framework.Capabilities import REMOTE
from _Framework.Capabilities import SCRIPT
from _Framework.Capabilities import controller_id
from _Framework.Capabilities import inport
from _Framework.Capabilities import outport

try:
    from .bridge import CodexBridge
except ImportError:
    from bridge import CodexBridge


def get_capabilities():
    return {
        CONTROLLER_ID_KEY: controller_id(
            vendor_id=0x7D7D,
            product_ids=[0x0001],
            model_name="Codex_AI",
        ),
        PORTS_KEY: [
            inport(props=[NOTES_CC, REMOTE, SCRIPT]),
            outport(props=[REMOTE, SCRIPT]),
        ],
        AUTO_LOAD_KEY: True,
    }


def create_instance(c_instance):
    try:
        c_instance.log_message("Codex_AI create_instance called")
    except Exception:
        pass
    return CodexBridge(c_instance)
