grammar FrameworkSpec;

// ============================================================
// The framework-spec DSL — model of a test-automation framework.
// Project DSL per DSL-First §2.4 (Kernel cannot carry spellings
// as data). SPEC-taf-v1-002-02 is the metamodel document.
// ============================================================

start
    : 'framework' NAME 'version' NUMBER decl* EOF
    ;

decl
    : 'vocabulary' '{' entry* '}'
    | 'locators'   '{' entry* '}'
    ;

entry
    : ('form' | 'rung') NAME '{' member* '}'
    ;

member
    : 'arg' NAME argType?
    | 'caption' STRING
    | 'key' NAME
    | 'python' STRING
    | 'java' STRING
    | 'variants' '{' variant* '}'
    | 'lines' '{' langLine* '}'
    | 'wrap' '{' wrapLine* '}'
    ;

argType
    : NAME
    | STRING
    ;

variant
    : 'on' (NAME (',' NAME)*)? '{' langLine* '}'
    ;

langLine
    : ('python' | 'java') STRING
    ;

wrapLine
    : ('python' | 'java') ('pre' | 'post') STRING
    ;

// ============================================================
// LEXER RULES
// ============================================================

NAME
    : [A-Za-z_][A-Za-z0-9_.:/-]*
    ;

NUMBER
    : [0-9]+
    ;

STRING
    : '"""' .*? '"""'              // raw triple-quoted — spellings
    | '"' ('\\"' | ~["\r\n])* '"'
    ;

COMMENT
    : '#' ~[\r\n]* -> skip
    ;

WS
    : [ \t\r\n]+ -> skip
    ;
