# How to Update the Documentation

The documentation can be found at [dtcontrol.readthedocs.io](https://dtcontrol.readthedocs.io/). The source files are located in this gitlab file, i.e. [https://gitlab.lrz.de/i7/dtcontrol/-/tree/master/docs](https://gitlab.lrz.de/i7/dtcontrol/-/tree/master/docs).

## Option 1: Make small changes directly

This option is only recommended to make small, individual changes to the documentation. Pushing to the master branch will directly update the documentation linked to the latest release version, which is display by default. Different versions can be selected at the bottom of the sidebar in the documentation.

Simply change the respective source file, commit and push the update as one would for any other project file. Make sure to include "#nobump" at the end of the commit message to prevent Read the Docs from incrementing the version number and creating a respective tag in gitlab.

The update then works the following way:
1. When a push is detected by gitlab, a webhook is triggered. (It should be visible in the left sidebar -> Settings -> Webhooks. However, you need at least the Maintainer role to view project settings.)
2. Read the Docs receives the event via the webhook.
3. Read the Docs starts a job to build the docs and publishes it automatically.


## Option 2: Create a new branch for the updates

This is the recommended option for more thorough changes.

1. Create a new project branch.
2. For this step, access to the Read the Docs settings is needed: In the Versions tab, add the new branch as an active version (Versions -> Activate a version).
3. Now, the new branch can be selected at the bottom of the left sidebar in the documentation. The changes made on the new branch can be inspected here.
4. At the end, merge the new branch with the main branch to add the updates to the main version.


## Note
Please feel free to edit this README with further information and comments regarding the documentation.
