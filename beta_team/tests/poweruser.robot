*** Settings ***
Library    SeleniumLibrary

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
