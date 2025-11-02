// Temporary file to test lint failure
// This file intentionally has linting errors

const unused_variable = "test"  // eslint error: unused variable

function badFunction( ) {  // eslint error: spacing
  console.log("test")
}

// Missing semicolons
const x = 1
const y = 2

export {}  // Make this a module
