# Installation Test

## For the user

1. **Conversation A** — send: `Take the test. @.cursor/installation_test/INSTRUCTIONS.md`
2. **Conversation B** — send: `Score the test. @.cursor/installation_test/INSTRUCTIONS.md`
3. Open `TEST_SCORE.md` to review.
4. To re-run:
   ```
   chmod 644 .cursor/installation_test/ANSWER_KEY.md .cursor/installation_test/questions/q*.md
   rm -rf .cursor/installation_test/answers/ .cursor/installation_test/scores/ .cursor/installation_test/TEST_SCORE.md
   ```

---

## For the agent

### If asked to "take the test"

1. Run: `chmod 000 .cursor/installation_test/ANSWER_KEY.md`
2. Run: `chmod 000 .cursor/installation_test/questions/q*.md`
3. Read `.cursor/installation_test/TEST.md` and follow its instructions.

### If asked to "score the test"

1. Run: `chmod 644 .cursor/installation_test/ANSWER_KEY.md`
2. Read `.cursor/installation_test/ANSWER_KEY.md` and follow its instructions.
