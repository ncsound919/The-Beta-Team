*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BUILD_PATH}    ${EMPTY}
*** Test Cases ***
Edge Case Testing
    Open Browser    ${BUILD_PATH}    chrome
    Test Invalid Inputs
    Test Large File Upload
    Test Network Disconnect
    Test Memory Pressure

*** Keywords ***
Test Invalid Inputs
    Input Text    id=email    invalid@@email
    Click Element    id=submit
    Page Should Contain    Invalid email
