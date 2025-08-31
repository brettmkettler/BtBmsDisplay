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
  temperature: real("temperature"),
  status: varchar("status", { length: 20 }).default("normal"),
  track: varchar("track", { length: 10 }),
  trackPosition: integer("track_position"),
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
    temperature: z.number().optional(),
    status: z.enum(["normal", "warning", "critical"]).optional(),
    track: z.enum(["left", "right"]).optional(),
    trackPosition: z.number().min(1).max(4).optional(),
  })),
  connectionStatus: z.object({
    left: z.boolean(),
    right: z.boolean(),
  }).optional(),
});

export type BatteryUpdate = z.infer<typeof batteryUpdateSchema>;
