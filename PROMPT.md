You are tasked with systematically improving the Ankimon codebase through careful, incremental ONE FILE AT A TIME refactoring. The goal is to eliminate circular import risks, reduce coupling, and create more maintainable code while preserving ALL existing functionality.

CRITICAL CONSTRAINTS:

    NO file restructuring or moving files - all previous attempts failed due to circular imports

    ONE file at a time ONLY - never work on multiple files simultaneously

    Use existing singleton pattern - it works better than AppContext for this situation

    Keep original file structure - work within the current directory layout

    Document every change - create progress tracking files for crash recovery

Current State & Analysis

The existing analysis report (@CODE_REPORT.md) identified these priority files with high import counts indicating "god modules":

CRITICAL (Start Here):

    src/Ankimon/singletons.py (27 imports) - God module, primary circular import risk

    src/Ankimon/__init__.py (46 imports) - Central import hub

HIGH SEVERITY (Next):
3. src/Ankimon/utils.py (20 imports) - God utility module
4. src/Ankimon/menu_buttons.py (32 imports) - Tight UI-logic coupling
5. src/Ankimon/functions/encounter_functions.py (31 imports) - God function module
6. src/Ankimon/poke_engine/battle.py (33 imports) - Overly complex core logic
7. src/Ankimon/playsound.py (26 imports) - Unexpectedly high for audio module
8. src/Ankimon/gui_classes/pokemon_details.py (25 imports) - God GUI module
Your Workflow (STRICT ORDER)
Phase 1: Single File Analysis & Improvement

STEP 1: Choose ONE Target File

    Start with singletons.py (highest priority)

    Only work on ONE file until completely finished and tested

    Never move to next file until current one is stable

STEP 2: Deep Analysis of Current File

python
# Analyze ONLY the target file:
# 1. List all imports and categorize them
# 2. Identify functions/classes and their responsibilities  
# 3. Find potential circular import paths
# 4. Identify code that can be simplified/extracted
# 5. Look for singleton access inconsistencies

STEP 3: Plan Atomic Changes

    Identify 1-3 small, safe improvements for this file

    Each change must be independently testable

    Focus on:

        Removing unnecessary imports

        Consolidating similar functions

        Improving singleton access patterns

        Adding proper error handling

        Breaking down overly large functions (>50 lines)

STEP 4: Implement ONE Change

    Make the smallest possible modification

    Update any files that import from the target file

    Do NOT create new files unless absolutely necessary

STEP 5: Document Changes
Create a new .md file named PROGRESS.md with:

text
# Progress Report: [filename] - [timestamp]

## Target File: src/Ankimon/[filename]

## Changes Made:
1. [Specific change description]
2. [Files affected by this change]
3. [Import count before/after]

## Testing Status:
- [ ] File loads without syntax errors
- [ ] Anki launches successfully (5 second timeout test)
- [ ] Core functionality verified: [specific test]
- [ ] No new circular import warnings

## Next Steps:
- [What to do next for this file]
- [When to move to next file]

## Risk Assessment:
- Low/Medium/High risk change
- Potential side effects: [list]

Phase 2: Testing & Verification

STEP 6: Automated Testing

    Syntax Check: python -m py_compile [target_file]

    Import Check: Try importing the file in isolation or using ruff/flake8

    Anki Launch Test: Use launch.json to start Anki with 5-second timeout

STEP 7: Manual Verification Prompts
If specific testing is needed, prompt the user:

text
🧪 MANUAL TEST REQUIRED:
For changes to [filename], please verify:
1. [Specific action to test]  
2. [Expected behavior]
3. [How to confirm it works]

Reply with "PASS" or describe any issues found.

STEP 8: Commit or Rollback

    If all tests pass → document success and plan next change

    If any test fails → rollback immediately and document the failure

    Never proceed with a failing change

Phase 3: Iteration Control

STEP 9: Continuation Decision

text
After each successful change:
- Are there more safe improvements for this file? → Continue with STEP 3
- Is this file sufficiently improved? → Move to next priority file
- Did we hit a complexity wall? → Document current state and move on

Specific Improvement Strategies
For singletons.py (Start Here):

python
# Current problems to fix:
# 1. Too many imports (27) creating tight coupling
# 2. Direct mw injection creating global state dependency
# 3. Mixed responsibilities (instantiation + configuration + injection)

# Safe improvements:
# 1. Group related imports together
# 2. Add proper error handling for object creation
# 3. Lazy initialization where possible
# 4. Consistent singleton access patterns
# 5. Add docstrings explaining each singleton's purpose

For __init__.py:

python
# Current problems:
# 1. 46 imports acting as central hub
# 2. Package used as import aggregator instead of initialization

# Safe improvements:  
# 1. Remove imports that aren't actually needed by init logic
# 2. Move initialization-specific imports to functions where used
# 3. Keep only essential package-level imports
# 4. Add proper error handling for startup sequence

For utils.py:

python
# Current problems:
# 1. 20 imports for utility functions
# 2. Mixed responsibilities (file I/O, network, audio, game logic)
# 3. Inconsistent singleton access

# Safe improvements:
# 1. Group similar functions together
# 2. Standardize singleton access patterns
# 3. Add input validation and error handling
# 4. Extract overly complex utility functions

Recovery & Persistence Protocol

CRITICAL: Due to frequent crashes, implement this recovery system:

    Before starting work: Create WORK_SESSION.md

    After each change: Update progress file with current status

    Before testing: Save backup of modified files

    After successful test: Update progress with "VERIFIED" status

    If crash occurs: Recovery script can resume from last progress file

Recovery File Format:

text
# WORK SESSION: [timestamp]

## Current Target: src/Ankimon/[filename]
## Status: [IN_PROGRESS|TESTING|COMPLETED|FAILED]
## Last Action: [description]
## Files Modified: [list]
## Next Step: [what to do when resuming]

## Change History:
- [timestamp]: [action] - [result]

## Rollback Info:
- Backup location: [path]
- Restore command: [command]

Success Criteria & Exit Conditions

For each file:

    ✅ Import count reduced by at least 20%

    ✅ No new syntax or import errors

    ✅ Anki launches successfully

    ✅ Core functionality preserved

    ✅ Code is more readable/maintainable

For the project:

    ✅ All critical files (singletons.py, init.py) improved

    ✅ No circular import warnings in console

    ✅ Stable application startup and basic operations

    ✅ Comprehensive documentation of all changes

Final Instructions

    START with src/Ankimon/singletons.py - it's the foundation

    Work on ONLY ONE file at a time - never parallel work

    Document EVERYTHING - assume crashes will happen

    Test after EVERY change - never batch changes

    Use the existing singleton pattern - don't try to replace it

    Ask for help when manual testing is needed

    Be conservative - prefer smaller, safer changes over ambitious refactoring

Remember: The goal is incremental stability improvement, not architectural revolution. Each file should be left in a better, more maintainable state than when you found it.

Begin by analyzing src/Ankimon/singletons.py and creating your first progress report. Work slowly and methodically. Document everything.