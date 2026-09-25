import SwiftUI

/// Paste box (B4) + "transform what you just copied?" (M6).
struct TransformView: View {
    @State private var text = ""
    @State private var showSheet = false
    @State private var clipboardOffer: String?

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 12) {
                if let c = clipboardOffer {
                    HStack {
                        Text("Transform what you just copied? (\(c.count) characters)").font(.callout)
                        Spacer()
                        Button("Yes") { text = c; clipboardOffer = nil; showSheet = true }
                        Button("No") { clipboardOffer = nil }.foregroundStyle(.secondary)
                    }.padding(10).background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))
                }
                TextEditor(text: $text).frame(minHeight: 220).padding(6)
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(.quaternary))
                    .overlay(alignment: .topLeading) {
                        if text.isEmpty { Text("Paste the article, post, or thread you're reading…").foregroundStyle(.tertiary).padding(12).allowsHitTesting(false) }
                    }
                Text("\(text.count) characters (min 200)").font(.caption).foregroundStyle(.secondary)
                Button { showSheet = true } label: { Label("Work the magic", systemImage: "sparkles").frame(maxWidth: .infinity) }
                    .buttonStyle(.borderedProminent).disabled(text.count < 200)
                Spacer()
            }
            .padding()
            .navigationTitle("RetAInize")
            .onAppear {
                if CommandLine.arguments.contains("-autorun") { text = Sample.text; showSheet = true; return }
                if UIPasteboard.general.hasStrings, let s = UIPasteboard.general.string, s.count >= 200, s != text { clipboardOffer = s }
            }
            .sheet(isPresented: $showSheet) {
                SheetView(text: text, source: "app-paste") { showSheet = false }
            }
        }
    }
}

enum Sample {
    static let text = """
    I've been at my company for about two years and things are mostly fine, but my manager has cancelled or moved our one-on-one six times in the last two months. Every time it's a last-minute message: sorry, something came up, let's do next week. Next week it happens again.

    I don't think she's doing it on purpose. She got two more direct reports in the spring and her calendar is a disaster. But the effect on me is real. I have a promotion case I want to build and I can't get twenty minutes to talk about it. Small decisions that need her sign-off are stalling.

    What I've tried: I sent a short agenda ahead of the last two meetings so she'd see there was something concrete. Didn't help. I asked if a different day would work better. She said Thursdays, then cancelled Thursday.

    How do I bring this up without sounding like I'm complaining about her workload, which she can't change?
    """
}
