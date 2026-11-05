import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export default function WalletScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1d3d63', '#12938d']} style={styles.hero}>
        <Text style={styles.balLabel}>💰 موجودی کیف پول</Text>
        <Text style={styles.balValue}>۰ <Text style={styles.balCur}>تومان</Text></Text>
        <View style={styles.balRow}>
          <View style={styles.balItem}>
            <Text style={styles.balItemVal}>۰ ت</Text>
            <Text style={styles.balItemLbl}>در انتظار</Text>
          </View>
          <View style={styles.balItem}>
            <Text style={styles.balItemVal}>۰ ت</Text>
            <Text style={styles.balItemLbl}>کل درآمد</Text>
          </View>
        </View>
      </LinearGradient>

      <View style={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 خدمات ارائه‌شده</Text>
          <View style={styles.empty}>
            <Ionicons name="receipt-outline" size={40} color="#dbe3ec" />
            <Text style={styles.emptyText}>هنوز خدماتی ثبت نشده</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7fa' },
  hero: { paddingTop: 50, paddingBottom: 24, paddingHorizontal: 24, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  balLabel: { color: 'rgba(255,255,255,0.8)', fontSize: 13, textAlign: 'center' },
  balValue: { color: '#fff', fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginTop: 4 },
  balCur: { fontSize: 14, opacity: 0.7 },
  balRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.2)' },
  balItem: { alignItems: 'center' },
  balItemVal: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  balItemLbl: { color: 'rgba(255,255,255,0.7)', fontSize: 10 },
  content: { padding: 16 },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 16, elevation: 2 },
  cardTitle: { fontSize: 15, fontWeight: 'bold', color: '#1d3d63' },
  empty: { alignItems: 'center', padding: 30 },
  emptyText: { color: '#94a3b8', fontSize: 14, marginTop: 8 },
});
