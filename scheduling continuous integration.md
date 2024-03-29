Edit the crontab for your user 
> codecrontab -e
		
This command opens the crontab file in your default text editor. If it's your first time using crontab, you might be prompted to select an editor.

Add a new line to the end of the file to define the schedule:javascriptCopy 

> code
> */15 * * * * /Users/communify/.jbi/continuous_integration.sh
		
*/15 * * * * specifies the schedule. In this case, it means "at every 15th minute".

/path/to/your/script.sh should be replaced with the actual path to your script.
Save the file and exit the editor.
If you're using vi or vim, you can press Esc, then type :wq, and press Enter.
If you're using nano, press Ctrl + O, Enter to save, and then Ctrl + X to exit.
Verify your cron job is scheduled:

> codecrontab -l
		
This command lists all cron jobs scheduled for your user account. You should see the line you just added.