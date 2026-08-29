export type Category =
  | "premium"
  | "stars"
  | "gift_new"
  | "gift_old"
  | "rent_number"
  | "rent_username"
  | "rent_nft";

export interface CatalogItem {
  id: number;
  category: Category;
  title: string;
  description: string | null;
  price_uzs: string;
  image_url: string | null;
  tags: string[] | null;
  discount_percent: number;
  stock: number | null;
}

export interface Order {
  id: number;
  catalog_item_id: number;
  item_title: string;
  qty: number;
  total_uzs: string;
  status: string;
  created_at: string;
}

export interface Transaction {
  id: number;
  type: string;
  amount_uzs: string;
  currency: string;
  status: string;
  created_at: string;
}

export interface Me {
  id: number;
  tg_id: number;
  username: string | null;
  first_name: string | null;
  language: "uz" | "ru" | "en";
  balance: string;
  referral_code: string;
  referral_link: string;
}

export interface CardTopupResult {
  request_id: number;
  amount_uzs: string;
  card_number: string;
  card_holder: string;
  bot_deeplink: string;
}

export interface StarsTopupResult {
  stars: number;
  invoice_link: string;
}
