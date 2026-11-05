import React from 'react';
import { View, Text, StyleSheet, ScrollView, Linking, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export default function CaseDetailScreen({ route, navigation }) {
  const { hid, caseData } = route.params;
  const c = caseData || {};
  const score = c.score || 0;
  const isUrgent = score >= 600 || (c.flags && c.flags.length > 0);

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1d3d63', '#162d4a']} style={styles.header}>
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Ionicons name="chevron-forward" size={24} color="#fff" />
          </TouchableOpacity>
          <View>
            <Text style={styles.headerTitle}>{c.name || hid}</Text>
            <Text style={styles.headerSub}>{hid}</Text>
          </View>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content}>
        {/* Score Circle */}
        <View style={styles.scoreCard}>
          <View style={styles.scoreCircle}>
            <Text style={styles.scoreNum}>{score}</Text>
            <Text style={styles.scoreLbl}>از ۱۰۰۰</Text>
          </View>
          <Text style={styles.scoreLevel}>
            {score >= 600 ? 'سطح ۵ — بسیار شدید' : score >= 450 ? 'سطح ۴ — شدید' : score >= 300 ? 'سطح ۳ — متوسط' : 'سطح ۱-۲ — کم'}
          </Text>
        </View>

        {/* Info */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 اطلاعات پرونده</Text>
          <InfoRow label="نام" value={c.name || '—'} />
          <InfoRow label="موقعیت" value={c.location || '—'} />
          <InfoRow label="استان" value={c.province || '—'} />
          <InfoRow label="اعضا" value={`${c.members || 0} نفر`} />
          <InfoRow label="وضعیت" value={c.status || 'در انتظار'} />
        </View>

        {/* Flags */}
        {c.flags && c.flags.length > 0 && (
          <View style={[styles.card, { borderRightColor: '#dc2626', borderRightWidth: 4 }]}>
            <Text style={styles.cardTitle}>🚩 نشانه‌های خطر</Text>
            {c.flags.map((f, i) => (
              <View key={i} style={styles.flagItem}>
                <Text style={styles.flagCode}>{f.code}</Text>
                <Text style={styles.flagTitle}>{f.title}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Actions */}
        <TouchableOpacity
          style={styles.reviewBtn}
          onPress={() => Linking.openURL(`http://188.212.96.235:8085/questionnaire/${hid}?role=assistant`)}
        >
          <LinearGradient colors={['#1d3d63', '#12938d']} style={styles.reviewGradient}>
            <Ionicons name="create" size={20} color="#fff" />
            <Text style={styles.reviewText}>📝 بازبینی پرسشنامه</Text>
          </LinearGradient>
        </TouchableOpacity>

        {/* Satisfaction */}
        <TouchableOpacity
          style={styles.satisfBtn}
          onPress={() => navigation.navigate('Satisfaction', { hid })}
        >
          <Ionicons name="star" size={20} color="#f59e0b" />
          <Text style={styles.satisfText}>⭐ ثبت رضایت‌سنجی</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

function InfoRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}:</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7fa' },
  header: { paddingTop: 50, paddingBottom: 16, paddingHorizontal: 20 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  headerSub: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  content: { padding: 16, paddingBottom: 40 },
  scoreCard: { alignItems: 'center', backgroundColor: '#fff', borderRadius: 16, padding: 24, marginBottom: 12, elevation: 3 },
  scoreCircle: {
    width: 100, height: 100, borderRadius: 50, borderWidth: 4, borderColor: '#1d3d63',
    alignItems: 'center', justifyContent: 'center',
  },
  scoreNum: { fontSize: 32, fontWeight: 'bold', color: '#1d3d63' },
  scoreLbl: { fontSize: 10, color: '#94a3b8' },
  scoreLevel: { fontSize: 14, color: '#1d3d63', fontWeight: '600', marginTop: 12 },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 16, marginBottom: 12, elevation: 2 },
  cardTitle: { fontSize: 15, fontWeight: 'bold', color: '#1d3d63', marginBottom: 12 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  infoLabel: { fontSize: 13, color: '#64748b' },
  infoValue: { fontSize: 13, fontWeight: '600', color: '#1a2b3c' },
  flagItem: { flexDirection: 'row', gap: 8, padding: 8, backgroundColor: '#fef2f2', borderRadius: 8, marginBottom: 6 },
  flagCode: { fontWeight: 'bold', color: '#dc2626', fontSize: 13 },
  flagTitle: { color: '#991b1b', fontSize: 13 },
  reviewBtn: { borderRadius: 12, overflow: 'hidden', marginBottom: 10 },
  reviewGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 14 },
  reviewText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  satisfBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: 14, borderWidth: 2, borderColor: '#f59e0b', borderRadius: 12,
  },
  satisfText: { color: '#f59e0b', fontSize: 15, fontWeight: '600' },
});
