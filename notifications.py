import dotenv, os, pyttsx3, pytz, datetime, genshin, asyncio, json, functools, psutil
from win11toast import toast_async
from time import localtime, strftime

ZZZn_path = os.path.dirname(os.path.realpath(__file__))
toast_async = functools.partial(toast_async, app_id="ZZZ Notifications", on_click=lambda args: None, on_dismissed=lambda args: None, on_failed=lambda args: None)
dotenv.load_dotenv(dotenv_path=f"{ZZZn_path}/settings.env")
zzz = genshin.Client()
engine = pyttsx3.init()
os.system("") # To make colors in errors always work
timezones = {"eu": "Etc/GMT-1", "as": "Etc/GMT-8", "us": "Etc/GMT+5"}

if os.path.exists("cache.json"):
    pass
else: 
    with open("cache.json", "w", encoding='utf-8') as cache_f:
        data = {
            'shiyu_season': 0
        }
        json.dump(data, cache_f, indent=4)

if os.getenv('set_cookies_method') == 'auto':
    zzz.set_browser_cookies()
elif os.getenv('set_cookies_method') == 'login':
    if os.getenv('ltuid') == 0 or os.getenv('ltoken') == "":
        print("\33[31mERROR | Incorrect ltuid or ltoken empty!\033[0m")
        exit()
    else:
        zzz.set_cookies(ltuid=int(os.getenv('ltuid')), ltoken=os.getenv('ltoken'))
else:
    print("\33[31mERROR | Incorrect value for \"set_cookies_method\"! \n\33[93mSet it to: \"login\" or \"auto\"\033[0m")
    exit()

if os.getenv("server") not in ["eu", "us", "as"]:
    print("\33[31mERROR | Incorrect value for \"server\"! \n\33[93mSet it to on of this values: \"eu\", \"us\", \"as\"\033[0m")
    exit()

def margin(input, margin, milestone):
    return any(int(x) <= input <= int(x) + margin for x in milestone)

def closest(input, milestone):
    return min(milestone, key=lambda x: abs(int(x) - input))

async def battery():
    battery_notification_send = False
    battery_last_count = -1
    battery_milestone_stop_notifications_until = -1
    icon = {
        'src': f'file://{ZZZn_path}/ico/Battery.ico',
        'placement': 'appLogoOverride'
    }
    while(True):
        ac = await zzz.get_game_accounts()
        for account in ac:
            if "nap" in account.game_biz:
                uid = account.uid
        notes = await zzz.get_zzz_notes(uid=uid)

        if battery_notification_send == True:
            if battery_last_count != notes.battery_charge.current:
                battery_notification_send = False
                if (os.getenv('battery_milestone')) == 'True':
                    if notes.battery_charge.current <= battery_milestone_stop_notifications_until:
                        battery_notification_send = True
                    else:
                        battery_milestone_stop_notifications_until = -1

        if (os.getenv('battery_milestone')) == 'True':
            battery_milestones = os.getenv('battery_milestones').split(', ')
            if margin(notes.battery_charge.current, int(os.getenv("battery_milestones_margin")), battery_milestones):
                if battery_notification_send == False:
                    print(f"{strftime('%H:%M:%S', localtime())} | One of your Battery Charge milestone was reached")
                    if os.getenv('tts') == 'True':
                        engine.say("One of your Battery Charge milestone was reached")
                        engine.runAndWait()
                    battery_last_count = notes.battery_charge.current
                    await toast_async("One of your Battery Charge milestone was reached", f"You currently have {notes.battery_charge.current} Battery Charge out of {notes.battery_charge.max}", icon=icon)
                    battery_notification_send = True
                    battery_milestone_stop_notifications_until = int(closest(notes.battery_charge.current, battery_milestones)) + int(os.getenv("battery_milestones_margin"))
            else:
                if battery_notification_send == False:
                    if notes.battery_charge.current == notes.battery_charge.max:
                        print(f"{strftime('%H:%M:%S', localtime())} | Your Battery Charge is FULL")
                        if os.getenv('tts') == 'True':
                            engine.say("Your Battery Charge is FULL")
                            engine.runAndWait()
                        battery_last_count = notes.battery_charge.current
                        await toast_async("Your Battery Charge is FULL", f"You currently have {notes.battery_charge.current} Battery Charge out of {notes.battery_charge.max}", icon=icon)
                        battery_notification_send = True
        else:
            if battery_notification_send == False:
                if notes.battery_charge.current == notes.battery_charge.max:
                    print(f"{strftime('%H:%M:%S', localtime())} | Your Battery Charge is FULL")
                    if os.getenv('tts') == 'True':
                        engine.say("Your Battery Charge is FULL")
                        engine.runAndWait()
                    battery_last_count = notes.battery_charge.current
                    await toast_async("Your Battery Charge is FULL", f"You currently have {notes.battery_charge.current} Battery Charge out of {notes.battery_charge.max}", icon=icon)
                    battery_notification_send = True

        await asyncio.sleep(480)

async def daily():
    daily_last_day = -1
    timezone = pytz.timezone('Etc/GMT-8')
    icon = {
        'src': f'file://{ZZZn_path}/ico/Daily.ico',
        'placement': 'appLogoOverride'
    }
    while (True):
        day = datetime.datetime.now(timezone).strftime('%d')

        if daily_last_day != day:
            try:
                reward = await zzz.claim_daily_reward(game=genshin.Game.ZZZ)
            except genshin.AlreadyClaimed:
                daily_last_day = day
            except genshin.DailyGeetestTriggered:
                url = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091"
                print(f"\33[31mERROR | Captcha Triggerd and script couldn't collect your daily! You have to collect it yourself here {url}\033[0m")
            else:
                print(f"{strftime('%H:%M:%S', localtime())} | Claimed daily reward - {reward.amount}x {reward.name}")
                if os.getenv('tts') == 'True':
                    engine.say("Collected your daily check-in reward")
                    engine.runAndWait()
                daily_last_day = day
                if os.getenv('daily_not') == 'True':
                    await toast_async("Collected your daily check-in reward", f"Claimed daily reward - {reward.amount}x {reward.name}", icon=icon)

        await asyncio.sleep(900)

async def shop():
    last_day = -1
    icon = {
        'src': f'file://{ZZZn_path}/ico/Shop.ico',
        'placement': 'appLogoOverride'
    }
    while(True):
        day = int(datetime.datetime.now(pytz.timezone(timezones[os.getenv("server")])).strftime('%d'))

        if last_day != day:
            last_day = day
            if day == 1:
                print(f"{strftime('%H:%M:%S', localtime())} | Shop has been reset today")
                if os.getenv('tts') == 'True':
                    engine.say("Shop has been reset today")
                    engine.runAndWait()
                await toast_async("Shop reset", f"Shop has been reset today", icon=icon)

        await asyncio.sleep(900)

shiyu_reset = False

async def shiyu():
    last_day = -1
    started_between_0_3 = False
    global shiyu_reset
    error = False
    icon = {
        'src': f'file://{ZZZn_path}/ico/Shiyu.ico',
        'placement': 'appLogoOverride'
    }
    while(True):
        day = int(datetime.datetime.now(pytz.timezone(timezones[os.getenv("server")])).strftime('%d'))
        hour = int(datetime.datetime.now(pytz.timezone(timezones[os.getenv("server")])).strftime('%H'))
        exe = True if hour >= 4 else False
        if (last_day != day and exe) or (not exe and not started_between_0_3 and day != last_day + 1):
            started_between_0_3 = not started_between_0_3
            last_day = day 

            ac = await zzz.get_game_accounts()
            for account in ac:
                if "nap" in account.game_biz:
                    uid = account.uid
            try:
                shiyu = await zzz.get_shiyu_defense(uid=uid)
                shiyu_old = await zzz.get_shiyu_defense(uid=uid, previous=True)
            except genshin.GeetestError as ex:
                print(f"\33[31mERROR | Captcha triggered while fetching Shiyu Defense data. Go to your Battle Chronicle and complete a captcha for the script to be able to notify you when Shiyu Defense resets!\033[0m")
                if os.getenv('tts') == 'True':
                    engine.say("Shiyu Defense reset data can't be collected! More information about the error is available in the console.")
                    engine.runAndWait()
                await toast_async("Shiyu Defense Error", f"Shiyu Defense reset data can't be collected!\nMore information about the error is available in the console.", icon=icon)
                return

            with open("cache.json", "r", encoding='utf-8') as cache_f:
                cache = json.load(cache_f)
                season = cache['shiyu_season']
                cache_f.close()
            
            if shiyu.schedule_id == 0 and shiyu_old.schedule_id == 0 and error == False:
                error = True
                print(f"\33[31mERROR | Shiyu Defense reset data can't be collected! If you haven't completed Shiyu Defense in the previous season, both `schedule_id` values are 0, making it impossible to check if the season has changed. Complete the current season, and going forward, you will receive notifications about season resets.\033[0m")
                if os.getenv('tts') == 'True':
                    engine.say("Shiyu Defense reset data can't be collected! More information about the error is available in the console.")
                    engine.runAndWait()
                await toast_async("Shiyu Defense Error", f"Shiyu Defense reset data can't be collected!\nMore information about the error is available in the console.", icon=icon)
            elif shiyu.schedule_id == 0 and shiyu_old.schedule_id != 0:
                if season != shiyu_old.schedule_id + 1:
                    with open("cache.json", "w", encoding='utf-8') as cache_f:
                        shiyu_reset = True
                        cache['shiyu_season'] = shiyu_old.schedule_id + 1
                        json.dump(cache, cache_f, indent=4)
                        cache_f.close()
                    print(f"{strftime('%H:%M:%S', localtime())} | Shiyu Defense has been reset")
                    if os.getenv('tts') == 'True':
                        engine.say("Shiyu Defense has been reset")
                        engine.runAndWait()
                    await toast_async("Shiyu Defense reset", f"Shiyu Defense has been reset", icon=icon)
            elif shiyu.schedule_id != 0 and shiyu.schedule_id != cache['shiyu_season']:
                with open("cache.json", "w", encoding='utf-8') as cache_f:
                    cache['shiyu_season'] = shiyu.schedule_id
                    json.dump(cache, cache_f, indent=4)
                    cache_f.close()

        await asyncio.sleep(900)

async def reminder():
    global shiyu_reset
    game_on = False
    icon_s = {
        'src': f'file://{ZZZn_path}/ico/Shop.ico',
        'placement': 'appLogoOverride'
    }
    icon_sh = {
        'src': f'file://{ZZZn_path}/ico/Shiyu.ico',
        'placement': 'appLogoOverride'
    }
    icon_v = {
        'src': f'file://{ZZZn_path}/ico/Video.ico',
        'placement': 'appLogoOverride'
    }
    icon_sc = {
        'src': f'file://{ZZZn_path}/ico/Scratch.ico',
        'placement': 'appLogoOverride'
    }
    while (True):
        name = "zenlesszonezero.exe" # "notepad++.exe"
        if name in (p.name().lower() for p in psutil.process_iter()):
            if game_on == False:
                game_on = True
                
                ac = await zzz.get_game_accounts()
                for account in ac:
                    if "nap" in account.game_biz:
                        uid = account.uid
                notes = await zzz.get_zzz_notes(uid=uid)

                if (int(os.getenv("reminder_additional_delay")) != 0):
                    await asyncio.sleep(int(os.getenv("reminder_additional_delay")))

                day = int(datetime.datetime.now(pytz.timezone(timezones[os.getenv("server")])).strftime('%d'))
                if os.getenv("reminder_shop") == "True":
                    if day == 1:
                        print(f"REMINDER {strftime('%H:%M:%S', localtime())} | Shop has been reset today")
                        if os.getenv('tts') == 'True':
                            engine.say("REMINDER Shop has been reset today")
                            engine.runAndWait()
                        await toast_async("Shop reset", f"Shop has been reset today", icon=icon_s)

                if os.getenv("reminder_shiyu") == "True":
                    if shiyu_reset:
                        print(f"REMINDER {strftime('%H:%M:%S', localtime())} | Shiyu Defense has been reset")
                        if os.getenv('tts') == 'True':
                            engine.say("REMINDER Shiyu Defense has been reset")
                            engine.runAndWait()
                        await toast_async("Shiyu Defense reset", f"Shiyu Defense has been reset", icon=icon_sh)

                if os.getenv("reminder_video") == "True":
                    if notes.video_store_state == genshin.models.VideoStoreState.REVENUE_AVAILABLE:
                        print(f"REMINDER {strftime('%H:%M:%S', localtime())} | Video Store can be collected")
                        if os.getenv('tts') == 'True':
                            engine.say("REMINDER Video Store can be collected")
                            engine.runAndWait()
                        await toast_async("Video Store completed", f"Video Store can be collected", icon=icon_v)
                    elif notes.video_store_state == genshin.models.VideoStoreState.WAITING_TO_OPEN:
                        print(f"REMINDER {strftime('%H:%M:%S', localtime())} | Video Store is closed!")
                        if os.getenv('tts') == 'True':
                            engine.say("REMINDER Video Store is closed! Open it to collect denies!")
                            engine.runAndWait()
                        await toast_async("Video Store closed", f"Video Store is closed!\nOpen it to collect denies!", icon=icon_v)

                if os.getenv("reminder_scratch") == "True":
                    if notes.scratch_card_completed == False:
                        print(f"REMINDER {strftime('%H:%M:%S', localtime())} | Scratch Card can be scratch")
                        if os.getenv('tts') == 'True':
                            engine.say("REMINDER Scratch Card can be scratch")
                            engine.runAndWait()
                        await toast_async("Scratch Card", f"Scratch Card can be scratch", icon=icon_sc)
        else:
            if game_on == True:
                game_on = False

        await asyncio.sleep(int(os.getenv("reminder_time")))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print("-----------------------------------")
    if (os.getenv('battery_not')) == 'True':
        task1 = asyncio.ensure_future(battery())
        print("Battery Charge turned on")
    if (os.getenv('daily_check_in')) == 'True':
        task2 = asyncio.ensure_future(daily())
        print("Daily check-in turned on")
    if (os.getenv('shop_not')) == 'True':
        task3 = asyncio.ensure_future(shop())
        print("Shop reset turned on")
    if (os.getenv('shiyu_not')) == 'True':
        task4 = asyncio.ensure_future(shiyu())
        print("Shiyu Defense reset turned on")
    if (os.getenv('reminder')) == 'True':
        task5 = asyncio.ensure_future(reminder())
        print('Reminders turned on:')
        if (os.getenv('reminder_shop')) == 'True':
            print("- Shop")
        if (os.getenv('reminder_shiyu')) == 'True':
            print("- Shiyu Defense")
        if (os.getenv('reminder_video')) == 'True':
            print("- Video Store")
        if (os.getenv('reminder_scratch')) == 'True':
            print("- Scratch Card")
    print("-----------------------------------")
    loop.run_forever()