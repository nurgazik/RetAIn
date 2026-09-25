import SwiftUI

struct RootView: View {
    @Environment(SessionState.self) private var session
    var body: some View {
        if session.signedIn {
            TabView {
                TransformView().tabItem { Label("RetAInize", systemImage: "sparkles") }
                WordsView().tabItem { Label("Words", systemImage: "character.book.closed") }
                ReadsView().tabItem { Label("My Reads", systemImage: "books.vertical") }
                SettingsView().tabItem { Label("Settings", systemImage: "gearshape") }
            }
        } else {
            SignInView()
        }
    }
}
