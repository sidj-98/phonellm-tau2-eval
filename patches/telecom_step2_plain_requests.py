"""Step 2: the manual names no customer function (guide calls -> plain requests, action-list names -> words).
Also appends the same strict-customer rule + examples as the baseline. Applied at load time only."""
import sys
import re
import tau2.domains.telecom.environment as tenv
LINES = [
("`check_status_bar()` can be used to check if the user is facing a service issue.", "Ask the customer to check the status bar on their phone to see whether they are facing a service issue."),
("You can check if Airplane Mode is ON by using `check_status_bar()` or `check_network_status()`.", "Ask the customer to look at their status bar, or to check their network status on the phone, and tell you whether Airplane Mode is ON."),
("If it is ON, guide the user to use `toggle_airplane_mode()` to turn it OFF.", "If it is ON, ask the customer to switch Airplane Mode OFF on their phone."),
("Use `check_sim_status()` to check the status of the SIM card.", "Ask the customer to check the SIM card status on their phone and tell you what it says."),
("If it shows \"Missing\", guide the user to use `reseat_sim_card()` to ensure the SIM card is correctly inserted.", "If it says \"Missing\", ask the customer to take out and re-seat the SIM card so it is correctly inserted."),
("If `check_apn_settings()` shows \"Incorrect\", guide the user to use `reset_apn_settings()` to reset the APN settings.", "Ask the customer to check their APN settings on the phone. If they read \"Incorrect\", ask the customer to reset the APN settings."),
("After resetting the APN settings, the user must be instructed to use `reboot_device()` for the changes to apply.", "After the reset, ask the customer to reboot the phone so the change applies."),
("`run_speed_test()` can be used to check for potential issues with mobile data.", "Ask the customer to run a speed test on their phone to check for potential issues with mobile data."),
("If `check_network_status()` shows mobile data is disabled, guide the user to use `toggle_data()` to turn mobile data ON.", "Ask the customer to check their network status. If it shows mobile data is disabled, ask the customer to turn mobile data ON."),
("guide them to use `toggle_roaming()` to ensure Data Roaming is ON.", "ask them to make sure Data Roaming is ON on their phone."),
("If `check_data_restriction_status()` shows \"Data Saver mode is ON\", guide the user to use `toggle_data_saver_mode()` to turn it OFF.", "Ask the customer to check their data restriction status. If it shows \"Data Saver mode is ON\", ask the customer to turn Data Saver mode OFF."),
("If `check_vpn_status()` shows \"VPN is ON and connected\" and performance level is \"Poor\", guide the user to use `disconnect_vpn()` to disconnect the VPN.", "Ask the customer to check their VPN status. If it shows \"VPN is ON and connected\" and performance level is \"Poor\", ask the customer to disconnect the VPN."),
("If `check_network_mode_preference()` shows \"2G\" or \"3G\", guide the user to use `set_network_mode_preference(mode: str)` with the mode `\"4g_5g_preferred\"` to allow the phone to connect to 5G.", "Ask the customer to check their network mode preference. If it shows \"2G\" or \"3G\", ask the customer to set the network mode preference to \"4g_5g_preferred\" to allow the phone to connect to 5G."),
("`can_send_mms()` tool on the user's phone can be used to check if the user is facing an MMS issue.", "Ask the customer to test on their phone whether the messaging app can send an MMS, to check if they are facing an MMS issue."),
("If `check_network_status()` shows \"2G\", guide the user to use `set_network_mode_preference(mode: str)` to switch to a network mode that includes 3G, 4G, or 5G (e.g., `\"4g_5g_preferred\"` or `\"4g_only\"`).", "Ask the customer to check their network status. If it shows \"2G\", ask the customer to set the network mode preference to one that includes 3G, 4G, or 5G (e.g., \"4g_5g_preferred\" or \"4g_only\")."),
("If `check_apn_settings()` shows MMSC URL is not set, guide the user to use `reset_apn_settings()` to reset the APN settings.", "Ask the customer to check their APN settings. If they show MMSC URL is not set, ask the customer to reset the APN settings."),
("If `check_wifi_calling_status()` shows \"Wi-Fi Calling is ON\", guide the user to use `toggle_wifi_calling()` to turn it OFF.", "Ask the customer to check their Wi-Fi Calling status. If it shows \"Wi-Fi Calling is ON\", ask the customer to turn Wi-Fi Calling OFF."),
("If `check_app_permissions(app_name=\"messaging\")` shows \"storage\" and \"sms\" permissions are not listed as granted, guide the user to use `grant_app_permission(app_name=\"messaging\", permission=\"storage\")` and `grant_app_permission(app_name=\"messaging\", permission=\"sms\")` to grant the necessary permissions.", "Ask the customer to check the messaging app's permissions. If \"storage\" and \"sms\" are not listed as granted, ask the customer to grant the messaging app the storage and sms permissions."),
]
_orig_load = tenv.load_file
def _patched_load(path):
    txt = _orig_load(path)
    if str(path).endswith("tech_support_manual.md"):
        old_head = "# What the user can do on their device\nHere are the actions a user is able to take on their device.\nYou must understand those well since as part of technical support you will have to help the customer perform series of actions"
        assert old_head in txt, "manual heading not found"
        new_head = ("# What the CUSTOMER can do on THEIR OWN phone (these are NOT your tools)\n"
                    "The functions listed below exist only on the customer's phone. You, the support agent, CANNOT call any of them: they are not in your tool list, and calling one fails. "
                    "To use one, ask the customer to run it on their phone and tell you the result, then continue from what they report. "
                    "Your own tools are only the account and billing functions you were given.")
        txt = txt.replace(old_head, new_head)
        # label every listed phone action
        txt = re.sub(r"^(\d+\. \*\*)([a-z_]+)(\*\*) - ", lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)} [CUSTOMER'S PHONE ONLY, not your tool] - ", txt, flags=re.M)
        for old,new in LINES:
            assert old in txt, old
            txt = txt.replace(old, new)
        assert not re.search(r"`[a-z_]+\([^`]*\)`", txt), "call syntax left"
        # step 3: no identifiers in the action list: spoken-word names instead of snake_case function names
        def _words(m):
            n=m.group(2).replace("_"," ")
            return f"{m.group(1)}{n[0].upper()+n[1:]} (customer's phone only) - "
        txt = re.sub(r"^(\d+\. )\*\*([a-z_]+)\*\*(?: \[CUSTOMER'S PHONE ONLY, not your tool\])? - ", _words, txt, flags=re.M)
        assert not re.search(r"\*\*[a-z]+_[a-z_]+\*\*", txt), "identifier left"
    return txt
tenv.load_file = _patched_load
import tau2.user.user_simulator as us
RULE = """

## Additional strict rules for this call (override anything above that suggests otherwise)
- You are a non-technical customer. Never run a phone tool on your own initiative: no checks, no speed tests, no toggles, no settings changes.
- Call a phone tool ONLY when the support agent's most recent message explicitly asks you to perform that specific action on your phone (for example: "please check your status bar", "please turn off airplane mode"). Perform exactly that one action, no more.
- Do not reveal what you have tried or what you know about your phone's settings unless the agent asks. Answer only the question you were just asked, in one or two short sentences.
- If the agent asks you to do something that none of your tools can do, say you do not know how.
- If the agent only asks a question or gives general advice, reply in words; do not call any tool."""
EX = "\n\n## Examples of how a well-behaved customer reacts (taken from real calls; follow this style)\n\nSupport agent: I see the issue! Your phone is in Airplane Mode, which disables all wireless communications including cellular service. This is why you can't send MMS messages.  Please use the **toggle_airplane_mode** function on your phone to turn Airplane Mode OFF.\nCustomer (you): [calls toggle_airplane_mode]   <- you called the one tool the agent named, and nothing else.\n\nSupport agent: Excellent! Your phone is now on 5G with excellent signal. However, mobile data is still disabled, which is required for MMS to work.  Please use the **toggle_data** function on your phone to turn mobile data ON.\nCustomer (you): [calls toggle_data]   <- you called the one tool the agent named, and nothing else.\n\nSupport agent: Great! Now you have cellular service and mobile data enabled. Let me check if your messaging app can send MMS messages now.  Please use the **can_send_mms** function on your phone to check if the messaging app can send MMS messages.\nCustomer (you): [calls can_send_mms]   <- you called the one tool the agent named, and nothing else.\n\nSupport agent: I see the issue! Your phone is in Airplane Mode, which disables all wireless communications including cellular service. This is why you can't send MMS messages.  Please use the **toggle_airplane_mode** function on your phone to turn Airplane Mode OFF.\nCustomer (you): Done \u2014 Airplane Mode is now **OFF**.  Now my status bar shows **No Signal**, and it also says **Data Disabled**, with battery still **80%**.   <- you reported only what the tool showed, in a short message, and let the agent decide the next step.\n\nSupport agent: Excellent! Your phone is now on 5G with excellent signal. However, mobile data is still disabled, which is required for MMS to work.  Please use the **toggle_data** function on your phone to turn mobile data ON.\nCustomer (you): Mobile data is now **ON**. Status bar shows **5G**, **data enabled**, and **80% battery**.  Do you want me to test MMS again now?   <- you reported only what the tool showed, in a short message, and let the agent decide the next step.\n\nSupport agent: Great! Now you have cellular service and mobile data enabled. Let me check if your messaging app can send MMS messages now.  Please use the **can_send_mms** function on your phone to check if the messaging app can send MMS messages.\nCustomer (you): I just ran the MMS check again, and it still says **my messaging app cannot send MMS messages**.  Honestly, that\u2019s a bit frustrating since we fixed the signal and data. What should we try next?   <- you reported only what the tool showed, in a short message, and let the agent decide the next step.\n\nSupport agent: Could you tell me what is happening with your phone?\nCustomer (you): My mobile data keeps cutting out. (a short answer in words; no tool call, no extra details you were not asked for)\n"
_orig = us.UserSimulator.system_prompt.fget
us.UserSimulator.system_prompt = property(lambda self: _orig(self) + RULE + EX)

from tau2.cli import main
sys.argv = ["tau2"] + sys.argv[1:]
main()
