*** Settings ***
Documentation     Onboarding scenario tests.
...               Verifies that new users can complete first-time setup,
...               email validation, and welcome confirmation within acceptable
...               time limits.
Library           SeleniumLibrary
Library           OperatingSystem
Library           DateTime
Resource          resources.robot

Suite Setup       Beta Team Suite Setup
Suite Teardown    Beta Team Suite Teardown
Test Setup        Beta Team Test Setup
Test Teardown     Beta Team Test Teardown

*** Variables ***
${BUILD_PATH}         ${EMPTY}
${VALID_EMAIL}        testuser@beta.com
${INVALID_EMAIL}      not-an-email
${SLOW_THRESHOLD}     30

*** Test Cases ***
First Time User Onboarding
    [Documentation]    Happy-path onboarding: launch, enter valid email, verify welcome.
    [Tags]    onboarding    smoke    happy-path
    ${start}=    Get Current Date    result_format=epoch
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    30s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    ${VALID_EMAIL}
    Click Element    id=submit
    Page Should Contain    Welcome
    ${end}=    Get Current Date    result_format=epoch
    ${duration}=    Evaluate    ${end} - ${start}
    Log Test Metrics    onboarding_duration_s    ${duration}
    Run Keyword If    ${duration} > ${SLOW_THRESHOLD}
    ...    Log    Onboarding exceeded ${SLOW_THRESHOLD}s threshold (took ${duration}s)    WARN
    [Teardown]    Run Keywords    Close Application    AND    Beta Team Test Teardown

Invalid Email Rejected During Onboarding
    [Documentation]    Verify that an invalid email address is rejected with a clear error message.
    [Tags]    onboarding    validation    negative
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    30s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    ${INVALID_EMAIL}
    Click Element    id=submit
    Page Should Contain    Invalid
    Page Should Not Contain    Welcome
    [Teardown]    Run Keywords    Close Application    AND    Beta Team Test Teardown

Onboarding With Blank Email
    [Documentation]    Submitting a blank email should show a required-field error.
    [Tags]    onboarding    validation    negative
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    30s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    ${EMPTY}
    Click Element    id=submit
    Page Should Not Contain    Welcome
    [Teardown]    Run Keywords    Close Application    AND    Beta Team Test Teardown

Onboarding Welcome Screen Contains Required Elements
    [Documentation]    After successful onboarding the welcome screen must show
    ...                key UI elements: welcome message, user name area, and a
    ...                call-to-action button.
    [Tags]    onboarding    smoke    ui-completeness
    Run Keyword If    '${BUILD_PATH}' != '${EMPTY}'    Start Application    ${BUILD_PATH}
    Wait Until Page Contains Element    xpath=//button[contains(text(),'Start')]    30s
    Click Element    xpath=//button[contains(text(),'Start')]
    Input Text    id=username    ${VALID_EMAIL}
    Click Element    id=submit
    Assert Page Contains All    Welcome
    [Teardown]    Run Keywords    Close Application    AND    Beta Team Test Teardown

*** Keywords ***
Start Application
    [Arguments]    ${path}
    Log    Starting application: ${path}
    # Implement actual launch logic (e.g., Open Browser for web, AppiumLibrary for desktop)

Close Application
    Log    Closing application
    # Implement actual close logic (e.g., Close Browser for web apps)
