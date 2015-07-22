* To create an executable version of this tool that can be copied to a VM and run
    * Set up a Google Sheet in your own account from [this](https://docs.google.com/spreadsheets/d1unqPOfrN1RiwGW6Od_4-mRBRyY9bGI1riMg_nJB1P1I/edit?usp=sharing) template
    * Clone this repository to your local machine
    * Move into the directory
    * Generate your own OAUTH2 credentials
        * Follow the instructions [here](http://gspread.readthedocs.org/en/latest/oauth2.html) up until the point where it says "Install oauth2client". Stop there - below steps will do this for you.
        * Copy the file that was generated to the data/google-credentials.json file in your cloned repository
    * Install [Vagrant](http://www.vagrantup.com) and [Virtualbox](https://www.virtualbox.org/wiki/Downloads)
    * Run ```build_artifact.sh```
* Copy the file release/artifacts/benchmark to any Linux host.
* Execute it on the host. It will copy test results to the spreadsheet you created.
  

