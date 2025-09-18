# Ankimon Refactoring Report: Incremental Improvements for Code Organization and Circular Import Prevention
This report outlines a comprehensive strategy for improving the Ankimon codebase, focusing on preventing circular imports and enhancing code organization through an incremental, file-by-file approach. This strategy is designed to address the issues identified during a recent large-scale restructuring attempt and provide actionable steps for a more stable and maintainable codebase.
## 1. Current State Assessment
A scan of all Python files in `src/Ankimon/` revealed several areas of concern, primarily related to module coupling, "god modules," and a high risk of circular imports. The following files have been identified as critical or high-severity offenders based on their import counts and observed responsibilities:
### Critical Offenders:
*   **`src/Ankimon/__init__.py` (46 imports)**: This file exhibits an extremely high number of imports, indicating it's being used as a central hub to expose a vast array of modules. This practice severely hinders modularity, makes dependency management opaque, and is a primary source of implicit circular dependencies. Its role should be limited to package initialization, not module aggregation.
*   **`src/Ankimon/singletons.py` (27 imports)**: This module acts as a "god module," instantiating nearly all core application objects (logger, settings, windows, Pokémon objects, etc.) and directly injecting them into Anki's main window (`mw`). This creates extremely tight coupling across the entire application, making it the most significant source of potential circular imports and difficult-to-manage dependencies. The module's own comment acknowledges its temporary nature, highlighting the need for its refactoring.
### High Severity Offenders (Potential God Modules / Hubs):
These files demonstrate an unusually high number of imports, suggesting they might be taking on too many responsibilities or acting as central points that pull in dependencies from many different parts of the application. This increases their risk of being involved in circular import chains and makes them difficult to maintain.
*   **`src/Ankimon/poke_engine/battle.py` (33 imports)**: While core battle logic is inherently complex, this many imports suggest it might be directly handling UI updates, data persistence, or other concerns that should ideally be delegated to other modules.
*   **`src/Ankimon/menu_buttons.py` (32 imports)**: This file likely defines GUI buttons and their associated actions. A high import count here indicates that button callbacks are directly invoking logic from many different modules, leading to tight coupling between the UI and various business logic components.
*   **`src/Ankimon/functions/encounter_functions.py` (31 imports)**: This module appears to be a collection of various functions related to Pokémon encounters. The high import count suggests it might be a "god function" module, containing disparate logic that should be broken down into more focused, smaller modules.
*   **`src/Ankimon/playsound.py` (26 imports)**: A module dedicated to sound playback should ideally have minimal dependencies. This high import count is unexpected and suggests it might be intertwined with other functionalities (e.g., settings, logging, specific game events) that could be decoupled.
*   **`src/Ankimon/gui_classes/pokemon_details.py` (25 imports)**: A GUI component for displaying Pokémon details should primarily focus on presentation. A large number of imports indicates it's likely fetching data, performing complex calculations, or interacting with various game systems directly, making it a "god module" for Pokémon information display.
*   **`src/Ankimon/pyobj/collection_dialog.py` (23 imports)**: Similar to `pokemon_details.py`, this dialog for managing the Pokémon collection is pulling in a significant number of dependencies, suggesting it's handling too many concerns (data management, UI, game logic).
*   **`src/Ankimon/pyobj/evolution_window.py` (23 imports)**: The evolution window's high import count points to tight coupling with game state, Pokémon data, and potentially UI elements beyond its direct responsibility.
*   **`src/Ankimon/pyobj/ankimon_sync.py` (22 imports)**: Synchronization logic often involves many components, but this high number of imports could indicate a lack of clear boundaries between the synchronization mechanism and the data it operates on, or the services it interacts with.
*   **`src/Ankimon/utils.py` (20 imports)**: This module is a general "catch-all" for various utility functions. While some utilities are necessary, a module with 20 imports and a wide range of unrelated functions (file system, network, Anki hooks, item management, sound effects, EV/IV calculations) is a strong candidate for being broken down into more specialized utility modules. Inconsistent access to singletons (e.g., `Settings()`, `ShowInfoLogger()`) was also observed, indicating a potential misunderstanding of singleton patterns or a need for dependency injection.
### Medium Severity:
*   **`src/Ankimon/config_var.py` (4 imports)**: This file serves as a collection of global configuration variables. Its primary concern is its direct and heavy reliance on `singletons.settings_obj`. While its role is clear, any refactoring of `singletons.py` will directly impact this file. The use of deferred imports for `playsound` is a good practice.
### Low Severity:
*   **`src/Ankimon/business.py` (3 imports)**: This module contains a mix of business logic and utility functions. While its import count is low, some functions could be extracted into more specific utility modules (e.g., `item_utils.py`, `game_math.py`) to improve cohesion.
## 2. Circular Import Risk Analysis
Although the basic import analysis did not detect direct `A -> B` and `B -> A` circular dependencies, the high number of imports in the identified "hub files" strongly suggests the presence of more complex circular import chains (e.g., `A -> B -> C -> A`).
**Key Risk Factors:**
*   **Hub Files**: Modules like `__init__.py`, `singletons.py`, `utils.py`, and various GUI/logic files act as central points, importing from many other modules. This creates a dense dependency graph where it's easy for a module to indirectly import something that eventually leads back to itself.
*   **Tight Coupling**: The direct instantiation of objects and injection into `mw` in `singletons.py` means that many parts of the application are implicitly aware of and dependent on each other. If a GUI component needs a `PokemonObject` and `PokemonObject` needs a `Logger` which is instantiated in `singletons.py`, and the GUI component is also instantiated in `singletons.py`, a cycle can easily form.
*   **Lack of Clear Layering**: The broad range of responsibilities in files like `utils.py` and `business.py` indicates a lack of clear architectural layering (e.g., UI layer, business logic layer, data access layer). When layers are not distinct, modules from different layers tend to import from each other indiscriminately, leading to cycles.
*   **Shared Utility Functions**: Many modules might import a common `utils.py` or `business.py`. If these utility modules then start importing from the modules that use them, a circular dependency is created.
## 3. Individual File Improvement Plan (Prioritized List)
This plan focuses on the most critical and high-severity offenders first, providing specific, actionable improvements for each. The goal is to make small, verifiable changes.
### Priority 1: Critical Hubs
1.  **`src/Ankimon/singletons.py` (Critical - God Module, Hub)**
    *   **Problem**: Instantiates almost all core objects, injects into `mw`, high coupling, primary source of circular import risk.
    *   **Improvement**:
        *   **Extract Object Instantiation**: Move the instantiation of specific objects (e.g., `logger`, `settings_obj`, `translator`, `main_pokemon`, `enemy_pokemon`, `trainer_card`, `ankimon_tracker_obj`, `shop_manager`, `pokedex_window`, `reviewer_obj`, `achievement_bag`, `data_handler_obj`, `data_handler_window`, `ankimon_tracker_window`, `evo_window`, `starter_window`, `item_window`, `pokecollection_win`, `pokemon_pc`) out of `singletons.py` into a dedicated application context or factory module.
        *   **Remove `mw` Injection**: Eliminate direct assignments to `mw` attributes (e.g., `mw.settings_ankimon = settings_window`). Instead, pass these objects as dependencies to functions or classes that need them.
        *   **Define Clear Interfaces**: For objects that are truly singletons (e.g., `Settings`, `Logger`), ensure they are accessed consistently via a dedicated `get_instance()` method or a dependency injection mechanism, rather than re-instantiating them or relying on global variables.
        *   **Goal**: Reduce `singletons.py` to a minimal module that perhaps only defines the `Settings` and `Logger` singletons, or is removed entirely in favor of a proper dependency injection system.
2.  **`src/Ankimon/__init__.py` (Critical - Central Import Hub)**
    *   **Problem**: Imports 46 modules, acting as a central aggregation point.
    *   **Improvement**:
        *   **Remove Excessive Imports**: Drastically reduce the number of imports. `__init__.py` should primarily be used for package-level initialization, not for importing and exposing every module within the package.
        *   **Explicit Imports**: Modules should import what they need directly, rather than relying on `__init__.py` to expose everything.
        *   **Goal**: Make `__init__.py` almost empty, or only contain imports for sub-packages.
### Priority 2: High Severity Hubs
3.  **`src/Ankimon/utils.py` (High - God Utility Module, Inconsistent Singleton Access)**
    *   **Problem**: Contains a wide range of unrelated utility functions, high import count, inconsistent singleton access.
    *   **Improvement**:
        *   **Extract Specialized Utility Modules**: Break down `utils.py` into smaller, more focused utility modules. Examples:
            *   `file_utils.py`: `check_folders_exist`, `check_file_exists`, `read_local_file`, `write_local_file`, `read_html_file`.
            *   `network_utils.py`: `test_online_connectivity`, `read_github_file`, `compare_files`.
            *   `item_utils.py`: `filter_item_sprites`, `random_item`, `daily_item_list`, `give_item`, `get_item_price`, `get_item_id`, `random_fossil`, `count_items_and_rewrite`, `get_item_description`.
            *   `pokemon_data_utils.py`: `format_pokemon_name`, `format_move_name`, `get_main_pokemon_data`, `load_collected_pokemon_ids`, `limit_ev_yield`, `iv_rand_gauss`, `get_ev_spread`, `get_tier_by_id`, `safe_get_random_move`.
            *   `audio_utils.py`: `play_effect_sound`, `play_sound`.
            *   `error_handling_utils.py`: `save_error_code`.
            *   `font_utils.py`: `load_custom_font`.
            *   `anki_integration_utils.py`: `addon_config_editor_will_display_json`, `close_anki`.
        *   **Consistent Singleton Access**: Ensure `Settings` and `ShowInfoLogger` are accessed consistently (e.g., always import the singleton instance from a dedicated `singletons.py` or pass them as arguments).
        *   **Goal**: Reduce `utils.py` to a minimal set of truly general-purpose utilities, or eliminate it entirely by distributing its functions into more cohesive modules.
4.  **`src/Ankimon/menu_buttons.py` (High - Tight UI-Logic Coupling)**
    *   **Problem**: High import count suggests direct coupling between UI actions and diverse application logic.
    *   **Improvement**:
        *   **Introduce Command Pattern/Event Bus**: Decouple button actions from direct logic calls. Instead of a button directly calling `some_game_logic_function()`, it could emit an event or execute a command object.
        *   **Dependency Injection for Callbacks**: Pass necessary logic objects (e.g., `battle_manager`, `collection_manager`) to the button constructors or callback setters, rather than importing them globally.
        *   **Goal**: Reduce imports by making `menu_buttons.py` primarily responsible for UI layout and event emission, with logic handled elsewhere.
5.  **`src/Ankimon/functions/encounter_functions.py` (High - God Function Module)**
    *   **Problem**: High import count, likely a collection of disparate functions related to encounters.
    *   **Improvement**:
        *   **Group by Sub-Domain**: Break down into smaller, more focused modules based on specific encounter sub-domains. Examples: `wild_pokemon_generation.py`, `capture_mechanics.py`, `flee_mechanics.py`, `encounter_ui_updates.py`.
        *   **Pass Dependencies**: Instead of importing everything, pass necessary objects (e.g., `main_pokemon`, `enemy_pokemon`, `settings`, `logger`) as arguments to functions.
        *   **Goal**: Create a more organized `functions/encounter/` subdirectory with specialized modules.
6.  **`src/Ankimon/poke_engine/battle.py` (High - Overly Complex Core Logic)**
    *   **Problem**: High import count, suggesting it handles too many aspects of a battle.
    *   **Improvement**:
        *   **Separate Concerns**: Distinguish between battle state management, battle calculations (damage, status effects), and battle event handling/logging.
        *   **Extract Sub-Components**: Create dedicated modules for `damage_calculation.py`, `status_effects.py`, `turn_management.py`, `battle_events.py`.
        *   **Dependency Injection**: Pass battle-related services (e.g., `logger`, `random_generator`, `move_data_provider`) rather than importing them globally.
        *   **Goal**: Make `battle.py` orchestrate the battle flow by coordinating with smaller, specialized modules.
7.  **`src/Ankimon/playsound.py` (High - Unexpectedly High Imports)**
    *   **Problem**: High import count for a sound module, suggesting it's doing more than just playing sounds.
    *   **Improvement**:
        *   **Isolate Sound Playback Logic**: Ensure `playsound.py` is solely responsible for playing audio files.
        *   **Decouple Settings/Logging**: If it's importing `Settings` or `Logger` to decide *whether* to play a sound or to log, these dependencies should be passed in or handled by a higher-level audio manager.
        *   **Goal**: Reduce imports to only what's necessary for audio playback.
8.  **`src/Ankimon/gui_classes/pokemon_details.py` (High - God GUI Module)**
    *   **Problem**: High import count for a GUI display component, indicating it's handling data fetching and complex logic.
    *   **Improvement**:
        *   **Separate Data from Presentation**: Introduce a dedicated "presenter" or "view model" layer that prepares data for the GUI. The GUI component should only receive pre-formatted data and display it.
        *   **Delegate Logic**: Any complex logic (e.g., calculating stats, fetching evolution chains) should be delegated to business logic modules, not handled directly within the GUI.
        *   **Goal**: Reduce imports to primarily GUI-related libraries and the presenter/view model.
9.  **`src/Ankimon/pyobj/collection_dialog.py` (High - God GUI Module)**
    *   **Problem**: High import count, handling data management, UI, and game logic.
    *   **Improvement**:
        *   **Separate Data Management**: Extract all data loading, saving, and manipulation logic into a dedicated `collection_manager.py` or `pokemon_repository.py`.
        *   **Delegate Game Logic**: Any game-specific logic (e.g., checking achievements, interacting with `reviewer_obj`) should be handled by appropriate business logic modules, with the dialog only triggering these actions.
        *   **Goal**: Make `collection_dialog.py` primarily responsible for displaying the collection and handling user input, delegating complex tasks.
10. **`src/Ankimon/pyobj/evolution_window.py` (High - Tight Coupling)**
    *   **Problem**: High import count, tightly coupled with game state, Pokémon data, and UI.
    *   **Improvement**:
        *   **Extract Evolution Logic**: Create a `pokemon_evolution_service.py` that handles all evolution-related calculations and state changes.
        *   **Event-Driven Updates**: The evolution window should trigger an evolution event, and other parts of the system (e.g., `main_pokemon` update) should react to this event, rather than the window directly manipulating them.
        *   **Goal**: Reduce imports by making the window primarily responsible for displaying evolution choices and animations, and triggering the evolution process.
### Priority 3: Medium Severity
11. **`src/Ankimon/config_var.py` (Medium - Singleton Dependency)**
    *   **Problem**: Heavy reliance on `singletons.settings_obj`.
    *   **Improvement**:
        *   **Refactor after `singletons.py`**: Once `singletons.py` is refactored to use a proper dependency injection or singleton pattern, `config_var.py` should be updated to access settings consistently.
        *   **Consider Alternatives**: If `config_var.py` becomes too large, consider organizing configuration into more specific configuration objects or classes.
        *   **Goal**: Ensure consistent and clean access to configuration values.
## 4. Circular Import Prevention Strategy
The core of preventing circular imports lies in establishing clear module boundaries, defining explicit dependencies, and adhering to architectural layering.
**Common Patterns Leading to Circular Imports in this Codebase:**
*   **"God Modules"**: Modules that try to do too much and import from everywhere.
*   **Implicit Global State**: Relying on `mw` or other global variables that are populated by one module and then accessed by many others.
*   **Bidirectional Dependencies**: Module A imports B, and B imports A (directly or indirectly).
*   **UI and Logic Intermingling**: GUI components directly importing and manipulating business logic, and business logic sometimes needing to update UI directly.
**Specific Techniques for Prevention:**
1.  **Dependency Inversion Principle (DIP) / Dependency Injection (DI)**:
    *   **Principle**: High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.
    *   **Application**: Instead of modules importing concrete implementations, they should depend on interfaces (abstract base classes or protocols). The concrete implementations are then "injected" at runtime.
    *   **Example**: Instead of `gui_component` importing `battle_logic`, `gui_component` depends on an `IBattleService` interface. The `BattleService` (concrete implementation) is passed to the `gui_component`'s constructor. This is crucial for breaking cycles between UI and business logic.
2.  **Deferred Imports (Import Inside Functions)**:
    *   **When to Use**: For imports that are only needed within a specific function or method, and not at the module level. This can break import cycles by delaying the import until it's actually needed, potentially after the importing module has finished initializing.
    *   **Caution**: Use sparingly, as it can make dependencies less obvious and slightly impact performance on first call. It's a tactical fix, not a strategic solution for poor design.
3.  **Creating Shared Utility Modules (Refined)**:
    *   **Principle**: Extract truly generic, stateless utility functions into dedicated, low-level modules that have no dependencies on the rest of the application.
    *   **Application**: As planned for `utils.py`, create modules like `file_utils.py`, `string_utils.py`, `math_utils.py`, etc. These modules should *never* import from higher-level application logic.
4.  **Event-Driven Architecture**:
    *   **Principle**: Modules communicate by emitting and listening for events, rather than direct function calls.
    *   **Application**: When a change in one module needs to notify another (e.g., `PokemonObject` evolves, `GUI` needs to update), the `PokemonObject` emits an `EvolutionEvent`, and the `GUI` listens for it. This decouples the modules, preventing direct import dependencies.
5.  **Clear Architectural Layering**:
    *   **UI Layer**: Responsible for presentation and user interaction. Should only import from the Business Logic Layer or Presentation Layer (View Models/Presenters).
    *   **Presentation Layer (View Models/Presenters)**: Prepares data for the UI. Imports from Business Logic Layer.
    *   **Business Logic Layer**: Contains core application rules and operations. Imports from Data Access Layer and Utility Layer.
    *   **Data Access Layer**: Handles persistence (reading/writing files, database). Should not import from higher layers.
    *   **Utility Layer**: Contains generic, stateless functions. Should have no dependencies on other application layers.
    *   **Application**: Enforce these layers. For example, GUI files (`gui_classes/`, `pyobj/` windows/dialogs) should not import directly from `poke_engine/` or `functions/` if those contain business logic. Instead, they should interact through an intermediary.
**Recommendations for Specific File Interactions:**
*   **GUI Files and Business Logic**: GUI files should *never* directly import business logic modules (e.g., `poke_engine/battle.py`, `functions/pokemon_functions.py`). Instead, they should interact with a "Controller" or "Presenter" that mediates between the UI and the business logic. The Controller/Presenter would import the business logic and expose a simplified interface to the GUI.
*   **`singletons.py` and `config_var.py`**: `singletons.py` should be refactored first. `config_var.py` should then access the `Settings` singleton via a consistent, well-defined method (e.g., `Settings.get_instance().get(...)`).
*   **`utils.py` and other modules**: Once `utils.py` is broken down, other modules should import only the specific utility functions they need from the new, smaller utility modules.
## 5. Incremental Workflow Design
The key to successful refactoring after a failed large-scale attempt is to make small, isolated changes that can be immediately verified.
**Step-by-Step Approach for Improving One File at a Time:**
1.  **Choose a Target File**: Select a file from the prioritized list (start with `singletons.py` or `__init__.py`).
2.  **Understand Current Dependencies**: Before making any changes, thoroughly understand what the target file imports and what other files import from it. Use the import analysis script and manual inspection.
3.  **Identify a Single, Atomic Change**: Focus on one specific improvement (e.g., extract one function, remove one unnecessary import, replace one global access with dependency injection).
4.  **Implement the Change**: Make the smallest possible code modification.
5.  **Update Dependent Files**: If the change affects how other files interact with the target file (e.g., a function was moved, an object is now injected), update those dependent files.
6.  **Run Tests**: Immediately run relevant unit tests and integration tests.
7.  **Manual Verification**: Perform manual checks of the affected functionality in the application.
8.  **Repeat**: Once verified, commit the change and move to the next atomic improvement.
**Testing Checkpoints for Each File Improvement:**
*   **Unit Tests**: If unit tests exist for the target file or its extracted components, run them. If not, consider writing minimal unit tests for the specific functionality being changed.
*   **Integration Tests**: Run integration tests that cover the functionality of the target file and its interactions with other modules.
*   **Application Startup**: Ensure the application still starts without errors after each change.
*   **Core Functionality Smoke Test**: Perform a quick manual check of the most critical features related to the changed file (e.g., if `battle.py` was changed, run a battle).
**Verification Strategy:**
*   **Automated Tests**: Prioritize writing and running automated tests.
*   **Linting/Static Analysis**: Run `ruff check .` (or similar) after each change to catch syntax errors, unused imports, and style violations.
*   **Type Checking**: If MyPy or a similar type checker is used, run it to ensure type consistency.
*   **Manual QA**: For UI-related changes, manual testing is crucial.
**Recommended Order of Operations:**
1.  **Refactor `singletons.py`**: This is foundational. Start by extracting objects and removing `mw` injections. This will likely involve creating new factory functions or a central application context.
2.  **Refactor `__init__.py`**: Reduce its imports.
3.  **Break Down `utils.py`**: Create specialized utility modules.
4.  **Address GUI-Logic Coupling**: Refactor `menu_buttons.py`, `pokemon_details.py`, `collection_dialog.py`, `evolution_window.py` by introducing presenters/controllers and dependency injection.
5.  **Modularize `functions/encounter_functions.py` and `poke_engine/battle.py`**: Break these down into smaller, more focused modules.
6.  **Clean Up `playsound.py` and `ankimon_sync.py`**: Isolate their core responsibilities.
7.  **Review `config_var.py`**: Update it to reflect the changes in `singletons.py`.
8.  **Address `business.py`**: Extract more specific functions if necessary.
## 6. Specific Questions Based on Past Issues
### How can we prevent the "god object" pattern we saw with AppContext?
The "god object" pattern, where a single object holds too many responsibilities and references to almost everything, leads to tight coupling and makes the system hard to change. To prevent this:
*   **Single Responsibility Principle (SRP)**: Each class or module should have only one reason to change. `AppContext` likely violated this by trying to manage settings, logging, UI components, and game state.
*   **Dependency Injection (DI)**: Instead of `AppContext` creating and holding references to all objects, objects should declare their dependencies, and these dependencies should be provided to them (injected) at creation time. This shifts the responsibility of object creation and wiring to a separate "composition root" (e.g., a main application setup function).
*   **Service Locator (with caution)**: A service locator can be used as an alternative to DI, where objects request their dependencies from a central registry. However, it can hide dependencies and lead to similar "god object" issues if not used carefully. Prefer DI.
*   **Clear Architectural Layers**: Enforce strict boundaries between layers. `AppContext` should not bridge all layers.
*   **Factories**: Use factory functions or classes to create complex objects, rather than having `AppContext` directly instantiate everything.
### What's the best way to handle the singletons pattern without circular imports?
The current `singletons.py` is problematic because it's not just defining singletons, but also instantiating and wiring up a large part of the application.
*   **True Singletons**: For objects that *truly* need to be singletons (e.g., `Settings`, `Logger`), implement them as proper singletons with a `get_instance()` method.
    ```python
    # Example of a proper Singleton
    class Settings:
        _instance = None
        def __new__(cls):
            if cls._instance is None:
                cls._instance = super(Settings, cls).__new__(cls)
                # Initialize settings here
                cls._instance.config = {} # Load from file etc.
            return cls._instance
        def get(self, key, default=None):
            return self.config.get(key, default)
    # Usage:
    settings_obj = Settings() # Or Settings.get_instance()
    ```
*   **Dependency Injection**: For most other objects that are currently treated as singletons in `singletons.py` (e.g., `PokemonObject`, `TrainerCard`, `TestWindow`), they are not true singletons. They are simply objects that are instantiated once. These should be created in a central "composition root" (e.g., `main.py` or an `app_factory.py`) and then passed as dependencies to other objects that need them.
*   **Avoid Global `mw` Injection**: Stop assigning objects directly to `mw` (e.g., `mw.settings_ankimon`). This creates global state and tight coupling. Pass these objects explicitly.
### How should GUI files import business logic without creating cycles?
This is a classic problem that can be solved with architectural patterns:
*   **Model-View-Presenter (MVP) or Model-View-ViewModel (MVVM)**:
    *   **View (GUI file)**: Passive, displays data, forwards user input to Presenter/ViewModel. Imports only from the Presentation Layer (Presenter/ViewModel).
    *   **Presenter/ViewModel**: Contains presentation logic, prepares data for the View, handles user input, interacts with the Business Logic Layer. Imports from Business Logic Layer.
    *   **Model (Business Logic)**: Contains core application logic and data. Does not import from View or Presenter/ViewModel.
    *   **Application**: GUI files (`gui_classes/`, `pyobj/` windows/dialogs) should import a `Presenter` or `ViewModel` (e.g., `PokemonDetailsPresenter`, `CollectionViewModel`). The Presenter/ViewModel then imports the actual business logic (e.g., `poke_engine/battle.py`, `functions/pokemon_functions.py`). This creates a unidirectional dependency: UI -> Presenter/ViewModel -> Business Logic.
*   **Command Pattern**: GUI buttons or actions can create and execute "Command" objects. These Command objects encapsulate the action and its parameters. The GUI doesn't need to know the details of the business logic; it just knows how to create and execute a command. The Command object then imports and interacts with the business logic.
### What's the cleanest way to handle the reviewer integration with Anki?
The Anki reviewer integration is a specific area that needs careful design to avoid tight coupling with the core Ankimon logic.
*   **Dedicated Anki Integration Layer**: Create a separate `anki_integration/` package. This package should contain all code that directly interacts with Anki's APIs (`aqt`, `mw`).
*   **Clear Interface for Ankimon**: The `anki_integration` layer should expose a clear, minimal interface to the rest of the Ankimon application. Ankimon should not directly import `aqt` or `mw` outside of this layer.
*   **Event-Driven Communication**: When Anki events occur (e.g., card reviewed, reviewer opened), the `anki_integration` layer should translate these into Ankimon-specific events and emit them. Ankimon's core logic can then listen to these events.
*   **Dependency Injection for Anki Services**: If Ankimon needs to *trigger* Anki actions (e.g., show a message in the reviewer), it should depend on an `IAnkiService` interface, and the concrete `AnkiService` (implemented in `anki_integration`) would be injected.
*   **Reviewer IFrame**: The `functions/reviewer_iframe.py` suggests using an iframe. This is a good approach for isolating the Ankimon UI within the Anki reviewer. Ensure the communication between the iframe and the main Ankimon application is well-defined (e.g., via JavaScript bridges or message passing) and doesn't create direct Python import cycles.
## Architectural Principles to Prevent Future Circular Import Issues
1.  **Single Responsibility Principle (SRP)**: Each module/class should have one, and only one, reason to change.
2.  **Open/Closed Principle (OCP)**: Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification. Use interfaces and dependency injection.
3.  **Liskov Substitution Principle (LSP)**: Objects in a program should be replaceable with instances of their subtypes without altering the correctness of that program. (Less directly related to imports, but good for overall design).
4.  **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on interfaces they do not use. Create small, specific interfaces rather than large, general-purpose ones.
5.  **Dependency Inversion Principle (DIP)**: High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions. This is the most crucial principle for preventing circular imports.
6.  **Acyclic Dependencies Principle (ADP)**: The dependency graph of packages or modules should not contain cycles.
7.  **Common Closure Principle (CCP)**: Classes that change together belong together.
8.  **Common Reuse Principle (CRP)**: Classes that are used together should be packaged together.
9.  **Release Reuse Equivalency Principle (REP)**: The granule of reuse is the granule of release.
By diligently applying these principles, especially DIP and ADP, the Ankimon codebase can evolve into a more modular, maintainable, and robust system, free from the complexities and fragility introduced by circular imports.