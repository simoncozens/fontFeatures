" Vim syntax file
" Language: Font Engineering with Extensions
" Maintainer: Simon Cozens
" Latest Revision: 27 January 2021

if exists("b:current_syntax")
  finish
endif

syn match comment "#.*$" 
syn match className "@[a-zA-Z0-9_\.~]\+"
syn match bareGlyph "\<[a-zA-Z0-9\.\-_]\+\>" contained
syn match uniGlyph "\<U+[0-9A-Fa-f]\+\>" 
syn match regexp "\/.*\/"
syn match arrow "\->"
syn match notAFeature "\<.*\>" contained
syn match featureName "\<[a-z0-9]\{4\}\>" contained
syn match traditionalValueRecord '<\(-\?[0-9]\+ \)\{3\}-\?[0-9]\+>'
syn match feeValueRecord '<\( *[xy]\(Advance\|Placement\)=-\?[0-9]\+ *\)\+>'
syn match language "<[a-zA-Z\/,\*]\+>"
syn match variable "\$[a-zA-Z0-9_]\+"

syn keyword groupKeywords Routine 
syn keyword featureKeyword Feature nextgroup=notAFeature,featureName skipwhite
syn keyword topLevelKeywords LoadPlugin
syn keyword otherKeywords Substitute Position Anchor Chain
syn region block start="{" end="}" fold transparent 
syn region glyphClass start="\[" end="\]" fold transparent contains=uniGlyph,regexp,className

syn keyword classDefinition DefineClass DefineClassBinned 

let b:current_syntax = "fee"

hi def link topLevelKeywords Statement
hi def link groupKeywords Keyword
hi def link featureKeyword Keyword
hi def link classDefinition Statement
hi def link otherKeywords Statement
hi def link className Identifier
hi def link bareGlyph String
hi def link variable Identifier
hi def link comment Comment
hi def link featureName Tag
hi def link notAFeature Error
hi def link uniGlyph String
hi def link regexp Type
hi def link language PreProc
hi def link integer Number
hi def link traditionalValueRecord Constant
hi def link feeValueRecord Constant
hi def link arrow Operator
