import Foundation
import UserNotifications

/// The daily practice nudge (D56): a local notification, offered once after the first finished
/// session, switchable in Settings. Nothing leaves the phone.
enum PracticeReminder {
    static let id = "practice-daily"
    private static let defaults = UserDefaults.standard

    /// Whether the app has already offered the reminder (it asks once).
    static var asked: Bool {
        get { defaults.bool(forKey: "practiceReminderAsked") }
        set { defaults.set(newValue, forKey: "practiceReminderAsked") }
    }
    static var isOn: Bool { defaults.bool(forKey: "practiceReminderOn") }

    @discardableResult
    static func enable(hour: Int = 19) async -> Bool {
        let center = UNUserNotificationCenter.current()
        guard (try? await center.requestAuthorization(options: [.alert, .sound])) == true else { return false }
        let content = UNMutableNotificationContent()
        content.title = "Today's words are ready"
        content.body = "A few minutes of practice keeps them yours."
        let trigger = UNCalendarNotificationTrigger(dateMatching: DateComponents(hour: hour), repeats: true)
        try? await center.add(UNNotificationRequest(identifier: id, content: content, trigger: trigger))
        defaults.set(true, forKey: "practiceReminderOn")
        return true
    }

    static func disable() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [id])
        defaults.set(false, forKey: "practiceReminderOn")
    }
}
