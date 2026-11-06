---
id: CONCEPT-junit-v1-003-01-assertall-grouped-assertions
status: accepted
subproject: junit
layer: L2-tool
since: JUnit 5.10
standing: recommended
realizes: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
contrasts-with: CONCEPT-pwtest-v1-003-01-expect-soft-and-poll
---

# Grouped Soft Assertions via assertAll

## Definition

JUnit Jupiter's `Assertions.assertAll` groups multiple assertion lambdas into a single execution block. 

Unlike standard "hard" assertions—which throw an `AssertionError` immediately upon the first failed condition and abort the remainder of the test method—`assertAll` executes every supplied `Executable` closure regardless of intermediate failures. If one or more assertions fail, `assertAll` bundles them together and throws a single `MultipleFailuresError` listing every violation and its distinct stack trace.

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class UserProfileTest {

    @Test
    void verifiesCompleteUserPayload() {
        User user = UserService.fetchUser(42);

        // All assertions execute even if the first one fails
        assertAll("User profile fields verification",
                () -> assertNotNull(user.getId(), "User ID must not be null"),
                () -> assertEquals("Jordan", user.getFirstName(), "First name mismatch"),
                () -> assertEquals("Lee", user.getLastName(), "Last name mismatch"),
                () -> assertEquals("jordan.lee@example.com", user.getEmail(), "Email mismatch"),
                () -> assertEquals(UserRole.ADMIN, user.getRole(), "User role mismatch")
        );
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-007-01-hard-vs-soft-assertions`. In complex verification scenarios—such as inspecting large domain objects, API response payloads, or multi-field form outputs—a single failure in an early assert statement prematurely hides failures in subsequent assertions. This forces engineers into an inefficient cycle of fixing one defect, rerunning the test, discovering the next defect, and repeating.

Contrasts with `CONCEPT-pwtest-v1-003-01-expect-soft-and-poll`. In Playwright Test, soft assertions are imperative statements (`expect.soft(locator).toBeVisible()`) where test code continues linearly until test end, at which point accumulated failures are reported. JUnit's `assertAll` uses structured functional closures (`Executable...`), establishing an explicit lexical boundary for grouped assertions while maintaining standard exception semantics outside the block.
