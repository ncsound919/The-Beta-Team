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
    ${duration}=    Evaluate    ${end}-${start}
    Log    Onboarding took ${duration} seconds
    [Teardown]    Close Application

*** Keywords ***
Start Application
    [Arguments]    ${path}
    Log    Starting application: ${path}
    # Placeholder: implement application start logic based on your app type

Close Application
    Log    Closing application
    # Placeholder: implement application close logic based on your app type
