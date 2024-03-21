# nanog-api-troubleshooting
Scripts that go along with the talk "Simplified Troubleshooting Through API Scripting" that was presented at NANOG 87 by Cat Gurinsky on Monday, February 13th, 2023. This talk was updated and presented again at the Network Automation Forum inaugural conference AutoCon0 on November 14th, 2023.

View the NANOG 87 talk here: https://www.youtube.com/watch?v=ne_4-5rdL_M
View the updated AutoCon0 Network Automation Forum Talk here: https://www.youtube.com/watch?v=BYAwFvWvDiE

View the NANOG 87 version of the slides here: https://storage.googleapis.com/site-media-prod/meetings/NANOG87/4617/20230213_Gurinsky_Simplified_Troubleshooting_Through_v1.pdf

## Full Abstract
How often do you find yourself doing the same set of commands when troubleshooting issues in your network? I am willing to bet the answer to this is quite often! Usually we have a list of our favorite commands that we will always use to quickly narrow down a specific problem type.

Switch reloaded unexpectedly? "show reload cause"
Fan failure? "show environment power"
Fiber link reporting high errors or down on your monitoring system? "show interface counters errors", "show interface transceiver", "show interface mac detail"

Outputs like the above examples help you quickly pinpoint the source of your failures for remediation. SSH'ing into the boxes and running these commands by hand is time consuming, especially if you are for example a NOC dealing with numerous failures throughout the day. Most switch platforms have API's now and you can instead program against them to get these outputs in seconds. I will go over a variety of examples and creative ways to use these scripts for optimal use of your troubleshooting time and to get you away from continually doing these repetitive tasks by hand.

NOTE: My tutorial examples will be using python and the Arista pyeapi module with Arista examples, but the concepts can easily be transferred to other platforms and languages.
