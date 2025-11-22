VAN: Based on @0001-system-design.md please initialize the memory bank under ./.cursor/memory. The tauri project has been setup

ok I've made refactor to the code. I've made a new lib crate ./vault-core which contains all functionalities so that ./src-tauri crate could focus on desktop app related stuff. Please carefully review the code in both crates You should follow my code and design pattern. BTW, I've also removed list all prompts functionality, we don't need that. There shouldn't be a view that user would want to browse all prompts at the moment. So please try not add it back. Once you understand the code, please let me know.

I've refactored @commands.rs please make sure you follow my code pattern. Now next task.
