*** Settings ***
Documentation     Shared keyword library for Beta Team test suites.
...               Provides reusable keywords for setup, teardown, validation,
...               timing, and evidence collection.
Library           OperatingSystem
Library           Collections
Library           String
Library           DateTime

*** Variables ***
${REPORT_DIR}         ${CURDIR}${/}..${/}reports
${SCREENSHOT_DIR}     ${REPORT_DIR}${/}screenshots
${TIMING_THRESHOLD}   30    # seconds before a step is flagged as slow

*** Keywords ***
Beta Team Suite Setup
    [Documentation]    Common suite-level setup: ensure output directories exist.
    Create Directory    ${REPORT_DIR}
    Create Directory    ${SCREENSHOT_DIR}
    Log    Suite started at ${REPORT_DIR}    console=True

Beta Team Suite Teardown
    [Documentation]    Log suite completion and persist any collected metrics.
    Log    Suite teardown complete    console=True

Beta Team Test Setup
    [Documentation]    Per-test setup: record start timestamp.
    ${now}=    Get Current Date    result_format=%Y-%m-%dT%H:%M:%S
    Set Test Variable    ${TEST_START_TIME}    ${now}

Beta Team Test Teardown
    [Documentation]    Per-test teardown: log final status.
    Log    Test finished with status: ${TEST_STATUS}

Verify Element Exists
    [Documentation]    Assert that a UI element is visible within the timeout.
    [Arguments]    ${locator}    ${timeout}=10s
    Wait Until Page Contains Element    ${locator}    timeout=${timeout}
    Element Should Be Visible    ${locator}

Click And Wait
    [Documentation]    Click an element and wait for a result element to appear.
    [Arguments]    ${trigger_locator}    ${result_locator}    ${timeout}=10s
    Click Element    ${trigger_locator}
    Wait Until Page Contains Element    ${result_locator}    timeout=${timeout}

Fill Field And Submit
    [Documentation]    Clear, fill, and submit a form field.
    [Arguments]    ${field_id}    ${value}    ${submit_id}
    Clear Element Text    id=${field_id}
    Input Text    id=${field_id}    ${value}
    Click Element    id=${submit_id}

Assert Page Contains All
    [Documentation]    Assert that all listed strings appear on the current page.
    [Arguments]    @{expected_texts}
    FOR    ${text}    IN    @{expected_texts}
        Page Should Contain    ${text}
    END

Measure Step Duration
    [Documentation]    Time a keyword call and log a warning if it exceeds the threshold.
    [Arguments]    ${keyword_name}    @{args}
    ${start}=    Get Current Date    result_format=epoch
    Run Keyword    ${keyword_name}    @{args}
    ${end}=    Get Current Date    result_format=epoch
    ${duration}=    Evaluate    ${end} - ${start}
    Run Keyword If    ${duration} > ${TIMING_THRESHOLD}
    ...    Log    SLOW STEP: ${keyword_name} took ${duration}s (threshold ${TIMING_THRESHOLD}s)    WARN
    [Return]    ${duration}

Log Test Metrics
    [Documentation]    Log a key=value metric for the current test.
    [Arguments]    ${key}    ${value}
    Log    METRIC | ${key}=${value}
