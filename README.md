# NikkeOLScraper
Outputs CSV of relevant OL stats per Nikke per player.

Requires players.csv in the following format:
Player,Link,UID
PROTO,MjkwODAtMTU3MDU5MTQyMjE5MzEzMDM4MjA=,29080-15705914221931303820
FAUST,MjkwODAtMzU0ODMxMjA5MjIwNTg4MTg1NA==,29080-3548312092205881854

Requires units.csv in the following format:
units/Name	units/Name code
Anis: Sparkling Summer	5097

Requires you to paste your blablalink cookie. Go to your blablalink, hit F12, under the Network tab find GetUserCharacters (or many others), on the right under Headers scroll down to your cookie. Copy the value of the cookie, should look like:
OptanonConsent=isGpcEnabled=0&...
