import SwiftUI
import UIKit

/// App-only parts of the notebook look (D70): the handwriting font (Caveat, SIL OFL 1.1, App/Fonts) and
/// the native navigation bar's titles. Extensions don't bundle the font, so these stay in the app.
extension Font {
    /// Handwriting, for screen titles and short notes only (it tires the eye in long text).
    static func hand(_ size: CGFloat, relativeTo style: Font.TextStyle = .title) -> Font {
        .custom("Caveat", size: size, relativeTo: style).weight(.bold)
    }
}

enum Theme {
    /// Large titles in handwriting, inline titles in SF Pro Rounded, both ink blue; the bar itself stays native.
    static func applyNavigationBar() {
        let hand = UIFontDescriptor(fontAttributes: [.family: "Caveat"]).withSymbolicTraits(.traitBold)
            ?? UIFontDescriptor(fontAttributes: [.family: "Caveat"])
        let rounded = UIFont.systemFont(ofSize: 17, weight: .bold).fontDescriptor.withDesign(.rounded)
        let ink = UIColor(Color.brandText)
        let bar = UINavigationBar.appearance()
        bar.largeTitleTextAttributes = [.font: UIFont(descriptor: hand, size: 44), .foregroundColor: ink]
        if let rounded { bar.titleTextAttributes = [.font: UIFont(descriptor: rounded, size: 17), .foregroundColor: ink] }
    }
}
