# visa-appointment-helper INFO
This script is not mine i just modified it's notification part
i simply change it to telegram chanel
It is modified for Kyiv located embassy


# visa-appointment-helper
A simple shell+python script to look for visa appointments

This script uses the human captcha solver service, [deathbycaptcha](http://deathbycaptcha.com/) as well as the excellent android integration tool [automate](http://llamalab.com/automate/) from llamalab to try look for a available appointment in German visa portal. Appointments are randomly made available when someone cancels and is therefore crucial to be intimated as soon as one is available.


### Installation

1. Copy this zip to any location and unzip everything into one folder while retaining the folder structure
2. change permissions on setup.sh using `chmod +x setup.sh`
3. Execute `./setup.sh`. This will give you the pre-requisites before you can run setup.
    * Edit the property in `setenv` file to the the root folder
    * Set execute permissions on all the scripts as well as executables
    * Comment out the echo messages and the exit command
4. Now, run `./setup.sh` to install pip and the required python dependencies. Make sure you have python3 installed before you run this


### Configure Android Phone for Notifications
open run.sh
edit line
curl -s -X POST https://api.telegram.org/bot<BOT TOKEN>/sendMessage -d chat_id=<CHAT ID> -d text=$available_date

Then put run.sh to cron

### Configurations
* The logic to determine if a available date is useful enough to notify the user is made in `lib/parse_response.py`. Edit it according to your requirements

### Enhancements
* Notify deathbycaptcha when captcha is wrong
* Automatically book appointment instead of just notifying
