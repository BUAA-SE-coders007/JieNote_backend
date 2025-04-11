# Release分支开发规范

大家好, 这里是运维coder0xe! 请大家在开发时遵守以下开发规范：

* 从 develop 分支检出，只用于发布前的确认；
* 允许从中分出 fix 分支，修复的 commit 需要 push 回 dev；
* ❌ 不允许开发者日常 push，只允许从 dev 合并。



feature 分支

* 从 dev 分支检出，用于新功能开发；
* 命名为 feature/name，如 feature/resume_generation；
* 开发完毕，经过测试后合并到 dev 分支；
* ✅ 允许开发者日常 push.

fix 分支

* 从 dev 或 release 分支检出，用于 bug 修复（feature 过程中的 bug 直接就地解决）；
* 特殊情况下允许直接从 main 直接开 fix 分支进行修复；
* 命名为 fix/issue_id，如 fix/2 ;
* 修复完毕，经过测试后合并到原来的分支（dev/release/main），并且保证同时合并到 dev;
* ✅ 允许开发者日常 push.

chore 分支

* 从 dev 分支检出，用于各项修正，如重构、风格优化等；
* 命名为 chore/name，如 chore/resume_generation；
* 开发完毕，经过测试后合并到 dev 分支；
* ✅ 允许开发者日常 push.


