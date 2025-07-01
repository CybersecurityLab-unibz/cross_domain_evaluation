const core = require('@actions/core');

try {
  const input = core.getInput('some-input');
  console.log(`Input received: ${input}`);
} catch (error) {
  core.setFailed(error.message);
}