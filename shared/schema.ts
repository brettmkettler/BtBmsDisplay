import { sql } from "drizzle-orm";
import { pgTable, text, varchar, real, integer, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const batteryData = pgTable("battery_data", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  batteryNumber: integer("battery_number").notNull(),
  voltage: real("voltage").notNull(),
  amperage: real("amperage").notNull(),
  chargeLevel: real("charge_level").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

export const insertBatteryDataSchema = createInsertSchema(batteryData).omit({
  id: true,
  timestamp: true,
});

export type InsertBatteryData = z.infer<typeof insertBatteryDataSchema>;
export type BatteryData = typeof batteryData.$inferSelect;

// WebSocket message types
export const batteryUpdateSchema = z.object({
  type: z.literal("battery_update"),
  batteries: z.array(z.object({
    batteryNumber: z.number().min(1).max(8),
    voltage: z.number().min(0).max(5),
    amperage: z.number().min(0).max(50),
    chargeLevel: z.number().min(0).max(100),
  })),
});

export type BatteryUpdate = z.infer<typeof batteryUpdateSchema>;
