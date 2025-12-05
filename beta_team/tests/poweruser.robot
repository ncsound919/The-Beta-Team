*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Power User Flow
    [Documentation]    Tests advanced user functionality
    Open Browser    ${BUILD_PATH}    chrome
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    10s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    poweruser@beta.com
    Click Element    id=submit
    Page Should Contain    Welcome
    # Power user specific actions
    Wait Until Page Contains Element    id=advanced-settings    10s
    Click Element    id=advanced-settings
    Page Should Contain    Advanced Options
    [Teardown]    Close Browser
