*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BUILD_PATH}    ${EMPTY}

*** Test Cases ***
Power User Workflow
    Open Application    ${BUILD_PATH}
    Login As Power User
    Create Complex Project
    Export Data
    Verify Export Success

*** Keywords ***
Login As Power User
    Input Text    id=poweruser    admin@beta.com
    Click Element    id=advanced

Create Complex Project
    Log    Creating complex project placeholder

Export Data
    Log    Exporting data placeholder

Verify Export Success
    Log    Verifying export success placeholder

Open Application
    [Arguments]    ${path}
    Log    Opening application: ${path}
