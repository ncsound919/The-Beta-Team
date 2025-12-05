*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Edge Cases
    [Documentation]    Tests edge cases for input validation
    Open Application    ${BUILD_PATH}
    Input Text    id=email    invalid@@email
    Click Element    id=submit
    Page Should Contain    Invalid email
    [Teardown]    Close Application
