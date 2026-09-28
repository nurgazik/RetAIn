import AppIntents

/// Siri phrases that work with no setup (D50). Every phrase must name the app.
struct RetAInShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: AddWordIntent(), phrases: [
            "Add a word to \(.applicationName)",
            "Add a new word to \(.applicationName)",
            "Save a word in \(.applicationName)",
            "Capture a word with \(.applicationName)",
        ], shortTitle: "Add Word", systemImageName: "plus.bubble")
    }
}
