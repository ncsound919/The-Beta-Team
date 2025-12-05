*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Onboarding Flow
    [Documentation]    Simulates first-time user
    Open Browser    ${BUILD_PATH}    chrome
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    10s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    testuser@beta.com
    Click Element    id=submit
    Page Should Contain    Welcome
    [Teardown]    Close Application
