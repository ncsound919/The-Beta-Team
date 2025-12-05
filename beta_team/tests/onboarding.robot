*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem

*** Variables ***
${BUILD_PATH}    ${EMPTY}

*** Test Cases ***
First Time User Onboarding
    ${start}=    Get Time    epoch
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    # NOTE: The following UI interactions require the application to be running.
    # The Start Application keyword above must be implemented first.
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
    # NOTE: This is a placeholder keyword. Implement actual application launch logic
    # based on your application type (e.g., Open Browser for web apps, or custom
    # keywords for desktop apps using AppiumLibrary or other libraries).

Close Application
    Log    Closing application
    # NOTE: This is a placeholder keyword. Implement actual application close logic
    # based on your application type (e.g., Close Browser for web apps).
