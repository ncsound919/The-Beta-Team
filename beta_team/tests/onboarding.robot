*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem

*** Variables ***
${BUILD_PATH}    ${EMPTY}

*** Test Cases ***
First Time User Onboarding
    ${start}=    Get Time    epoch
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    30s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    testuser@beta.com
    Click Element    id=submit
    Page Should Contain    Welcome
    ${end}=    Get Time    epoch
    Log    Onboarding took ${${end}-${start}} seconds
    [Teardown]    Close Application
