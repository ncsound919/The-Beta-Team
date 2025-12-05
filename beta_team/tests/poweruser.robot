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
    [Teardown]    Close Browser

*** Keywords ***
Open Application
    [Arguments]    ${build_path}
    Open Browser    ${build_path}    chrome
    Maximize Browser Window

Create Complex Project
    # Placeholder: Steps to create a complex project
    Click Element    id=create-project
    Input Text    id=project-name    Complex Project
    Click Element    id=submit-project

Export Data
    # Placeholder: Steps to export data
    Click Element    id=export-data

Verify Export Success
    # Placeholder: Verify export was successful
    Wait Until Page Contains    Export completed successfully
Login As Power User
    Input Text    id=poweruser    admin@beta.com
    Click Element    id=advanced
