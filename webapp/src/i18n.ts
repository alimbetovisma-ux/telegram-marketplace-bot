export type Lang = "uz" | "ru" | "en";

const STRINGS: Record<Lang, Record<string, string>> = {
  uz: {
    nav_market: "Market",
    nav_rent: "Ijara",
    nav_wallet: "Hamyon",
    nav_profile: "Profil",

    market_title: "Market",
    market_sub: "Xizmatni tanlang",
    rent_title: "Ijara",
    rent_sub: "Vaqtinchalik ijaraga oling",

    cat_premium: "Telegram Premium",
    cat_stars: "Telegram Stars",
    cat_gift_new: "Sovg'alar",
    cat_gift_old: "Noyob sovg'alar",
    cat_rent_number: "Raqamlar",
    cat_rent_username: "Usernamelar",
    cat_rent_nft: "NFT sovg'alar",

    empty_category: "Bu bo'limda hozircha tovarlar yo'q",
    loading: "Yuklanmoqda...",

    per_day: "/ kun",
    btn_buy: "Sotib olish",
    btn_rent: "Ijaraga olish",
    balance_label: "BALANS",
    som: "so'm",

    wallet_topup: "To'ldirish",
    wallet_withdraw: "Chiqarish",
    wallet_mine: "Mening",
    wallet_history: "Tarix",

    topup_title: "Hamyonni to'ldirish",
    topup_amount_label: "Miqdor (so'm)",
    topup_method_card: "Karta orqali",
    topup_method_stars: "Stars orqali",
    topup_get_card: "Karta raqamini olish",
    topup_or: "yoki",
    topup_pay_stars: "Stars bilan to'lash",
    topup_card_result_title: "Quyidagi kartaga o'tkazing",
    topup_card_holder: "Egasi",
    topup_go_to_bot: "Chekni yuborish uchun botga o'ting",
    topup_stars_opened: "To'lov oynasi ochildi...",
    topup_stars_success: "To'lov qabul qilindi! Balans yangilanmoqda...",
    topup_invalid_amount: "To'g'ri summa kiriting",

    withdraw_soon: "Chiqarish funksiyasi tez orada qo'shiladi. Admin bilan bog'laning.",

    orders_empty: "Buyurtmalar yo'q",
    history_empty: "Tranzaksiyalar yo'q",
    status_pending: "Kutilmoqda",
    status_confirmed: "Tasdiqlandi",
    status_rejected: "Rad etildi",
    status_paid_awaiting_fulfillment: "Yetkazilmoqda",
    status_fulfilled: "Yetkazildi",
    status_cancelled: "Bekor qilindi",

    profile_language: "Til",
    profile_referral_title: "Referal dasturi",
    profile_referral_desc: "Do'stingiz xariddan {percent}% bonus oling.",
    profile_copy: "Nusxalash",
    profile_copied: "Nusxalandi!",
    profile_my_orders: "Mening buyurtmalarim",

    buy_success: "Buyurtma qabul qilindi! Admin tez orada bog'lanadi.",
    buy_insufficient: "Balans yetarli emas",
    buy_confirm: "Xarid qilishni tasdiqlaysizmi?",

    close: "Yopish",
    back: "Orqaga",
  },
  ru: {
    nav_market: "Маркет",
    nav_rent: "Аренда",
    nav_wallet: "Кошелёк",
    nav_profile: "Профиль",

    market_title: "Маркет",
    market_sub: "Выберите услугу",
    rent_title: "Аренда",
    rent_sub: "Возьмите активы во временное пользование",

    cat_premium: "Telegram Premium",
    cat_stars: "Telegram Stars",
    cat_gift_new: "Подарки",
    cat_gift_old: "Редкие подарки",
    cat_rent_number: "Номера",
    cat_rent_username: "Юзернеймы",
    cat_rent_nft: "NFT-подарки",

    empty_category: "В этом разделе пока нет товаров",
    loading: "Загрузка...",

    per_day: "/ день",
    btn_buy: "Купить",
    btn_rent: "Арендовать",
    balance_label: "БАЛАНС",
    som: "сум",

    wallet_topup: "Пополнить",
    wallet_withdraw: "Вывести",
    wallet_mine: "Мои",
    wallet_history: "История",

    topup_title: "Пополнение кошелька",
    topup_amount_label: "Сумма (сум)",
    topup_method_card: "Картой",
    topup_method_stars: "Stars",
    topup_get_card: "Получить номер карты",
    topup_or: "или",
    topup_pay_stars: "Оплатить через Stars",
    topup_card_result_title: "Переведите на эту карту",
    topup_card_holder: "Получатель",
    topup_go_to_bot: "Перейти в бот, чтобы отправить чек",
    topup_stars_opened: "Окно оплаты открыто...",
    topup_stars_success: "Оплата принята! Обновляем баланс...",
    topup_invalid_amount: "Введите корректную сумму",

    withdraw_soon: "Функция вывода скоро появится. Свяжитесь с админом.",

    orders_empty: "Заказов нет",
    history_empty: "Транзакций нет",
    status_pending: "Ожидание",
    status_confirmed: "Подтверждено",
    status_rejected: "Отклонено",
    status_paid_awaiting_fulfillment: "Выдаётся",
    status_fulfilled: "Выдано",
    status_cancelled: "Отменено",

    profile_language: "Язык",
    profile_referral_title: "Реферальная программа",
    profile_referral_desc: "Получайте {percent}% бонус с покупок друга.",
    profile_copy: "Скопировать",
    profile_copied: "Скопировано!",
    profile_my_orders: "Мои заказы",

    buy_success: "Заказ принят! Админ скоро свяжется с вами.",
    buy_insufficient: "Недостаточно средств",
    buy_confirm: "Подтвердить покупку?",

    close: "Закрыть",
    back: "Назад",
  },
  en: {
    nav_market: "Market",
    nav_rent: "Rent",
    nav_wallet: "Wallet",
    nav_profile: "Profile",

    market_title: "Market",
    market_sub: "Choose a service",
    rent_title: "Rent",
    rent_sub: "Rent assets temporarily",

    cat_premium: "Telegram Premium",
    cat_stars: "Telegram Stars",
    cat_gift_new: "Gifts",
    cat_gift_old: "Rare gifts",
    cat_rent_number: "Numbers",
    cat_rent_username: "Usernames",
    cat_rent_nft: "NFT gifts",

    empty_category: "No items in this section yet",
    loading: "Loading...",

    per_day: "/ day",
    btn_buy: "Buy",
    btn_rent: "Rent",
    balance_label: "BALANCE",
    som: "UZS",

    wallet_topup: "Top up",
    wallet_withdraw: "Withdraw",
    wallet_mine: "Mine",
    wallet_history: "History",

    topup_title: "Top up wallet",
    topup_amount_label: "Amount (UZS)",
    topup_method_card: "By card",
    topup_method_stars: "By Stars",
    topup_get_card: "Get card number",
    topup_or: "or",
    topup_pay_stars: "Pay with Stars",
    topup_card_result_title: "Transfer to this card",
    topup_card_holder: "Holder",
    topup_go_to_bot: "Go to the bot to send the receipt",
    topup_stars_opened: "Payment window opened...",
    topup_stars_success: "Payment accepted! Refreshing balance...",
    topup_invalid_amount: "Enter a valid amount",

    withdraw_soon: "Withdrawals are coming soon. Contact admin.",

    orders_empty: "No orders yet",
    history_empty: "No transactions yet",
    status_pending: "Pending",
    status_confirmed: "Confirmed",
    status_rejected: "Rejected",
    status_paid_awaiting_fulfillment: "Fulfilling",
    status_fulfilled: "Fulfilled",
    status_cancelled: "Cancelled",

    profile_language: "Language",
    profile_referral_title: "Referral program",
    profile_referral_desc: "Get {percent}% bonus on your friend's purchases.",
    profile_copy: "Copy",
    profile_copied: "Copied!",
    profile_my_orders: "My orders",

    buy_success: "Order placed! Admin will contact you shortly.",
    buy_insufficient: "Insufficient balance",
    buy_confirm: "Confirm purchase?",

    close: "Close",
    back: "Back",
  },
};

export function t(lang: Lang, key: string, vars?: Record<string, string | number>): string {
  let str = STRINGS[lang]?.[key] ?? STRINGS.uz[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      str = str.replace(`{${k}}`, String(v));
    }
  }
  return str;
}
