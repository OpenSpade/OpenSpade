from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


class NotificationType(Enum):
    SMS = "sms"
    VOICE = "voice"
    EMAIL = "email"
    DINGTALK = "dingtalk"
    TELEGRAM = "telegram"


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationMessage:
    title: str
    content: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NotificationChannel(ABC):
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sent_count: int = 0
        self.failed_count: int = 0

    @abstractmethod
    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def validate_config(self) -> Tuple[bool, str]:
        pass

    def get_stats(self) -> Dict[str, int]:
        return {
            "sent": self.sent_count,
            "failed": self.failed_count,
            "success_rate": self.sent_count / (self.sent_count + self.failed_count) if (self.sent_count + self.failed_count) > 0 else 0
        }


class SMSChannel(NotificationChannel):
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str],
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers

    def validate_config(self) -> Tuple[bool, str]:
        if not self.account_sid or not self.auth_token:
            return False, "Twilio credentials not configured"
        if not self.from_number:
            return False, "From number not configured"
        if not self.to_numbers:
            return False, "No recipient numbers configured"
        return True, "SMS configuration valid"

    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "SMS channel is disabled"

        valid, msg = self.validate_config()
        if not valid:
            self.failed_count += 1
            return False, msg

        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException

            client = Client(self.account_sid, self.auth_token)

            for to_number in self.to_numbers:
                twilio_message = client.messages.create(
                    body=f"{message.title}\n{message.content}",
                    from_=self.from_number,
                    to=to_number
                )

                if twilio_message.status == "failed":
                    self.failed_count += 1
                    return False, f"Failed to send SMS to {to_number}"

            self.sent_count += 1
            return True, f"SMS sent successfully to {len(self.to_numbers)} recipients"

        except ImportError:
            self.failed_count += 1
            return False, "Twilio library not installed. Run: pip install twilio"
        except Exception as e:
            self.failed_count += 1
            return False, f"SMS send error: {str(e)}"


class VoiceChannel(NotificationChannel):
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str],
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers

    def validate_config(self) -> Tuple[bool, str]:
        if not self.account_sid or not self.auth_token:
            return False, "Twilio credentials not configured"
        if not self.from_number:
            return False, "From number not configured"
        if not self.to_numbers:
            return False, "No recipient numbers configured"
        return True, "Voice configuration valid"

    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "Voice channel is disabled"

        valid, msg = self.validate_config()
        if not valid:
            self.failed_count += 1
            return False, msg

        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException

            client = Client(self.account_sid, self.auth_token)

            for to_number in self.to_numbers:
                call = client.calls.create(
                    twiml=f"<Response><Say voice='alice'>{message.content}</Say></Response>",
                    from_=self.from_number,
                    to=to_number
                )

                if call.status == "failed":
                    self.failed_count += 1
                    return False, f"Failed to make voice call to {to_number}"

            self.sent_count += 1
            return True, f"Voice call initiated successfully to {len(self.to_numbers)} recipients"

        except ImportError:
            self.failed_count += 1
            return False, "Twilio library not installed. Run: pip install twilio"
        except Exception as e:
            self.failed_count += 1
            return False, f"Voice call error: {str(e)}"


class EmailChannel(NotificationChannel):
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    def validate_config(self) -> Tuple[bool, str]:
        if not self.smtp_host or not self.smtp_port:
            return False, "SMTP server not configured"
        if not self.username or not self.password:
            return False, "SMTP credentials not configured"
        if not self.from_email:
            return False, "From email not configured"
        if not self.to_emails:
            return False, "No recipient emails configured"
        return True, "Email configuration valid"

    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "Email channel is disabled"

        valid, msg = self.validate_config()
        if not valid:
            self.failed_count += 1
            return False, msg

        try:
            msg_obj = MIMEMultipart("alternative")
            msg_obj["From"] = self.from_email
            msg_obj["To"] = ", ".join(self.to_emails)
            msg_obj["Subject"] = message.title
            msg_obj["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

            text_part = MIMEText(message.content, "plain")
            content_with_break = message.content.replace('\n', '<br>')
            html_part = MIMEText(
                f"""
                <html>
                <body>
                    <h2>{message.title}</h2>
                    <p>{content_with_break}</p>
                    <hr>
                    <p><small>Sent at: {datetime.now().isoformat()}</small></p>
                </body>
                </html>
                """,
                "html"
            )

            msg_obj.attach(text_part)
            msg_obj.attach(html_part)

            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            server.login(self.username, self.password)
            server.sendmail(self.from_email, self.to_emails, msg_obj.as_string())
            server.quit()

            self.sent_count += 1
            return True, f"Email sent successfully to {len(self.to_emails)} recipients"

        except ImportError:
            self.failed_count += 1
            return False, "SMTP library not available"
        except smtplib.SMTPAuthenticationError:
            self.failed_count += 1
            return False, "SMTP authentication failed"
        except smtplib.SMTPException as e:
            self.failed_count += 1
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            self.failed_count += 1
            return False, f"Email send error: {str(e)}"


class DingTalkChannel(NotificationChannel):
    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
        at_mobiles: Optional[List[str]] = None,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.webhook_url = webhook_url
        self.secret = secret
        self.at_mobiles = at_mobiles or []

    def validate_config(self) -> Tuple[bool, str]:
        if not self.webhook_url:
            return False, "DingTalk webhook URL not configured"
        return True, "DingTalk configuration valid"

    def _generate_sign(self, timestamp: int) -> str:
        if not self.secret:
            return ""

        import hashlib
        import hmac
        import base64

        string_to_sign = f"{timestamp}\n{self.secret}"
        hash = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
        sign = base64.b64encode(hash).decode("utf-8")
        return sign

    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "DingTalk channel is disabled"

        valid, msg = self.validate_config()
        if not valid:
            self.failed_count += 1
            return False, msg

        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            sign = self._generate_sign(timestamp)

            url = self.webhook_url
            if self.secret:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}timestamp={timestamp}&sign={sign}"

            priority_emoji = {
                NotificationPriority.LOW: "",
                NotificationPriority.NORMAL: "",
                NotificationPriority.HIGH: "🔶",
                NotificationPriority.URGENT: "🔴"
            }

            content = f"{priority_emoji.get(message.priority, '')}{message.title}\n\n{message.content}"

            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            if self.at_mobiles:
                payload["at"] = {
                    "atMobiles": self.at_mobiles,
                    "isAtAll": False
                }

            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

            result = response.json()

            if result.get("errcode") == 0:
                self.sent_count += 1
                return True, "DingTalk message sent successfully"
            else:
                self.failed_count += 1
                return False, f"DingTalk API error: {result.get('errmsg', 'Unknown error')}"

        except ImportError:
            self.failed_count += 1
            return False, "Requests library not installed. Run: pip install requests"
        except requests.RequestException as e:
            self.failed_count += 1
            return False, f"DingTalk request error: {str(e)}"
        except Exception as e:
            self.failed_count += 1
            return False, f"DingTalk send error: {str(e)}"


class TelegramChannel(NotificationChannel):
    def __init__(
        self,
        bot_token: str,
        chat_ids: List[str],
        api_url: Optional[str] = None,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_url = api_url or "https://api.telegram.org"

    def validate_config(self) -> Tuple[bool, str]:
        if not self.bot_token:
            return False, "Telegram bot token not configured"
        if not self.chat_ids:
            return False, "No chat IDs configured"
        return True, "Telegram configuration valid"

    def send(self, message: NotificationMessage) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "Telegram channel is disabled"

        valid, msg = self.validate_config()
        if not valid:
            self.failed_count += 1
            return False, msg

        try:
            priority_emoji = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.NORMAL: "📢",
                NotificationPriority.HIGH: "⚠️",
                NotificationPriority.URGENT: "🚨"
            }

            emoji = priority_emoji.get(message.priority, "📢")
            formatted_content = f"{emoji} *{message.title}*\n\n{message.content}"

            success_count = 0
            errors = []

            for chat_id in self.chat_ids:
                url = f"{self.api_url}/bot{self.bot_token}/sendMessage"

                payload = {
                    "chat_id": chat_id,
                    "text": formatted_content,
                    "parse_mode": "Markdown",
                    "disable_notification": message.priority == NotificationPriority.LOW
                }

                response = requests.post(url, json=payload, timeout=10)

                if response.status_code == 200:
                    success_count += 1
                else:
                    error_msg = response.json().get("description", "Unknown error")
                    errors.append(f"Chat {chat_id}: {error_msg}")

            if success_count > 0:
                self.sent_count += 1
                if errors:
                    return True, f"Sent to {success_count}/{len(self.chat_ids)} chats. Errors: {'; '.join(errors)}"
                return True, f"Telegram message sent successfully to {success_count} chats"
            else:
                self.failed_count += 1
                return False, f"Failed to send to all chats: {'; '.join(errors)}"

        except ImportError:
            self.failed_count += 1
            return False, "Requests library not installed. Run: pip install requests"
        except requests.RequestException as e:
            self.failed_count += 1
            return False, f"Telegram request error: {str(e)}"
        except Exception as e:
            self.failed_count += 1
            return False, f"Telegram send error: {str(e)}"


class NotificationManager:
    def __init__(self):
        self.channels: Dict[NotificationType, NotificationChannel] = {}
        self.notification_history: List[Dict] = []
        self.max_history: int = 100

    def add_channel(self, channel_type: NotificationType, channel: NotificationChannel) -> None:
        self.channels[channel_type] = channel

    def remove_channel(self, channel_type: NotificationType) -> bool:
        if channel_type in self.channels:
            del self.channels[channel_type]
            return True
        return False

    def get_channel(self, channel_type: NotificationType) -> Optional[NotificationChannel]:
        return self.channels.get(channel_type)

    def send(
        self,
        message: NotificationMessage,
        channel_types: Optional[List[NotificationType]] = None
    ) -> Dict[NotificationType, Tuple[bool, str]]:
        if channel_types is None:
            channel_types = list(self.channels.keys())

        results = {}

        for channel_type in channel_types:
            channel = self.channels.get(channel_type)
            if not channel:
                results[channel_type] = (False, f"Channel {channel_type.value} not configured")
                continue

            if not channel.enabled:
                results[channel_type] = (False, f"Channel {channel_type.value} is disabled")
                continue

            success, msg = channel.send(message)
            results[channel_type] = (success, msg)

            self._add_to_history(channel_type, message, success, msg)

        return results

    def send_to_all(self, message: NotificationMessage) -> Dict[NotificationType, Tuple[bool, str]]:
        return self.send(message, channel_types=list(self.channels.keys()))

    def _add_to_history(
        self,
        channel_type: NotificationType,
        message: NotificationMessage,
        success: bool,
        result_message: str
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel_type.value,
            "title": message.title,
            "content": message.content,
            "priority": message.priority.value,
            "success": success,
            "result": result_message
        }

        self.notification_history.append(entry)

        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]

    def get_history(
        self,
        channel_type: Optional[NotificationType] = None,
        limit: int = 20
    ) -> List[Dict]:
        history = self.notification_history

        if channel_type:
            history = [h for h in history if h["channel"] == channel_type.value]

        return history[-limit:]

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        stats = {}
        for channel_type, channel in self.channels.items():
            stats[channel_type.value] = channel.get_stats()
        return stats

    def validate_all_configs(self) -> Dict[NotificationType, Tuple[bool, str]]:
        results = {}
        for channel_type, channel in self.channels.items():
            results[channel_type] = channel.validate_config()
        return results


def create_notification_manager(
    sms_config: Optional[Dict] = None,
    voice_config: Optional[Dict] = None,
    email_config: Optional[Dict] = None,
    dingtalk_config: Optional[Dict] = None,
    telegram_config: Optional[Dict] = None
) -> NotificationManager:
    manager = NotificationManager()

    if sms_config and sms_config.get("enabled"):
        manager.add_channel(
            NotificationType.SMS,
            SMSChannel(
                account_sid=sms_config.get("account_sid", ""),
                auth_token=sms_config.get("auth_token", ""),
                from_number=sms_config.get("from_number", ""),
                to_numbers=sms_config.get("to_numbers", []),
                enabled=True
            )
        )

    if voice_config and voice_config.get("enabled"):
        manager.add_channel(
            NotificationType.VOICE,
            VoiceChannel(
                account_sid=voice_config.get("account_sid", ""),
                auth_token=voice_config.get("auth_token", ""),
                from_number=voice_config.get("from_number", ""),
                to_numbers=voice_config.get("to_numbers", []),
                enabled=True
            )
        )

    if email_config and email_config.get("enabled"):
        manager.add_channel(
            NotificationType.EMAIL,
            EmailChannel(
                smtp_host=email_config.get("smtp_host", ""),
                smtp_port=email_config.get("smtp_port", 587),
                username=email_config.get("username", ""),
                password=email_config.get("password", ""),
                from_email=email_config.get("from_email", ""),
                to_emails=email_config.get("to_emails", []),
                use_tls=email_config.get("use_tls", True),
                enabled=True
            )
        )

    if dingtalk_config and dingtalk_config.get("enabled"):
        manager.add_channel(
            NotificationType.DINGTALK,
            DingTalkChannel(
                webhook_url=dingtalk_config.get("webhook_url", ""),
                secret=dingtalk_config.get("secret"),
                at_mobiles=dingtalk_config.get("at_mobiles", []),
                enabled=True
            )
        )

    if telegram_config and telegram_config.get("enabled"):
        manager.add_channel(
            NotificationType.TELEGRAM,
            TelegramChannel(
                bot_token=telegram_config.get("bot_token", ""),
                chat_ids=telegram_config.get("chat_ids", []),
                api_url=telegram_config.get("api_url"),
                enabled=True
            )
        )

    return manager


if __name__ == "__main__":
    print("Notification Module initialized successfully!")

    manager = NotificationManager()

    manager.add_channel(
        NotificationType.DINGTALK,
        DingTalkChannel(
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
            secret="YOUR_SECRET",
            at_mobiles=["13800138000"],
            enabled=True
        )
    )

    test_message = NotificationMessage(
        title="Test Notification",
        content="This is a test message from the notification module.",
        priority=NotificationPriority.NORMAL
    )

    results = manager.send(test_message, [NotificationType.DINGTALK])

    for channel_type, (success, msg) in results.items():
        print(f"{channel_type.value}: {'✓' if success else '✗'} {msg}")
