*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Edge Cases
    [Documentation]    Tests edge cases for input validation
    Open Browser    ${BUILD_PATH}    chrome
    Input Text    id=email    invalid@@email
    Click Element    id=submit
    Page Should Contain    Invalid email
    [Teardown]    Close Browser
