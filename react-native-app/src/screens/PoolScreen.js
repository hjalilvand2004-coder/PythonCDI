import React, { useState, useEffect, useContext } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet, RefreshControl, Alert, Linking } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AppContext } from '../../App';
import { getPool, claimCase } from '../api';

export default function PoolScreen({ navigation }) {
  const [cases, setCases] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadCases = async () => {
    setRefreshing(true);
    const data = await getPool();
    setCases(data);
    setRefreshing(false);
  };

  useEffect(() => { loadCases(); }, []);

  const handleClaim = async (hid) => {
    Alert.alert('تخصیص', 'آیا این پرونده به شما تخصیص داده شود؟', [
      { text: 'انصراف', style: 'cancel' },
      {
        text: 'تخصیص',
        onPress: async () => {
          const ok = await claimCase(hid);
          if (ok) {
            // باز کردن پرسشنامه با داده پیش‌تکمیل
            Linking.openURL(`http://188.212.96.235:8085/questionnaire/${hid}?role=assistant`);
          } else {
            Alert.alert('خطا', 'تخصیص ناموفق');
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }) => {
    const isUrgent = item.score >= 600 || (item.flags && item.flags.length > 0);
    const borderColor = isUrgent ? '#dc2626' : item.score >= 300 ? '#f59e0b' : '#16a34a';

    return (
      <TouchableOpacity
        style={[styles.card, { borderRightColor: borderColor, borderRightWidth: 4 }]}
        onPress={() => navigation.navigate('CaseDetail', { hid: item.hid, caseData: item })}
        activeOpacity={0.9}
      >
        {/* Header */}
        <View style={styles.cardHeader}>
          <LinearGradient colors={['#1d3d63', '#12938d']} style={styles.avatar}>
            <Text style={styles.avatarText}>{(item.name || '?')[0]}</Text>
          </LinearGradient>
          <View style={styles.cardInfo}>
            <Text style={styles.cardName} numberOfLines={1}>{item.name || item.hid}</Text>
            <Text style={styles.cardLoc} numberOfLines={1}>📍 {item.location || 'نامشخص'}</Text>
          </View>
          <View style={styles.scoreBox}>
            <Text style={styles.scoreVal}>{item.score}</Text>
            <Text style={styles.scoreLbl}>امتیاز</Text>
          </View>
        </View>

        {/* Tags */}
        <View style={styles.tagsRow}>
          {item.flags && item.flags.length > 0 && (
            <View style={[styles.tag, { backgroundColor: '#fee2e2' }]}>
              <Text style={[styles.tagText, { color: '#991b1b' }]}>🚩 {item.flags.length} پرچم</Text>
            </View>
          )}
          <View style={[styles.tag, { backgroundColor: '#dbeafe' }]}>
            <Text style={[styles.tagText, { color: '#1e40af' }]}>👥 {item.members || 0} نفر</Text>
          </View>
          {isUrgent && (
            <View style={[styles.tag, { backgroundColor: '#fef3c7' }]}>
              <Text style={[styles.tagText, { color: '#92400e' }]}>فوری</Text>
            </View>
          )}
        </View>

        {/* Actions */}
        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.acceptBtn} onPress={() => handleClaim(item.hid)}>
            <Ionicons name="checkmark-circle" size={18} color="#fff" />
            <Text style={styles.acceptText}>تخصیص</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.viewBtn} onPress={() => navigation.navigate('CaseDetail', { hid: item.hid, caseData: item })}>
            <Ionicons name="eye" size={18} color="#fff" />
            <Text style={styles.viewText}>مشاهده</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1d3d63', '#162d4a']} style={styles.header}>
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Ionicons name="chevron-forward" size={24} color="#fff" />
          </TouchableOpacity>
          <View>
            <Text style={styles.headerTitle}>استخر درخواست‌ها</Text>
            <Text style={styles.headerSub}>{cases.length} پرونده در انتظار</Text>
          </View>
          <TouchableOpacity onPress={loadCases}>
            <Ionicons name="refresh" size={22} color="rgba(255,255,255,0.7)" />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <FlatList
        data={cases}
        renderItem={renderItem}
        keyExtractor={item => item.hid}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadCases} />}
        contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="checkmark-done-circle" size={48} color="#dbe3ec" />
            <Text style={styles.emptyText}>هیچ درخواستی در انتظار نیست</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7fa' },
  header: { paddingTop: 50, paddingBottom: 16, paddingHorizontal: 20 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  headerSub: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 12,
    shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 3,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  avatar: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  cardInfo: { flex: 1, marginLeft: 10 },
  cardName: { fontSize: 15, fontWeight: '700', color: '#1a2b3c' },
  cardLoc: { fontSize: 12, color: '#64748b', marginTop: 2 },
  scoreBox: { alignItems: 'center' },
  scoreVal: { fontSize: 20, fontWeight: 'bold', color: '#1d3d63' },
  scoreLbl: { fontSize: 9, color: '#94a3b8' },
  tagsRow: { flexDirection: 'row', gap: 6, marginBottom: 12, flexWrap: 'wrap' },
  tag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  tagText: { fontSize: 11, fontWeight: '600' },
  actionsRow: { flexDirection: 'row', gap: 8 },
  acceptBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, backgroundColor: '#16a34a', padding: 10, borderRadius: 10,
  },
  acceptText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  viewBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, backgroundColor: '#1d3d63', padding: 10, borderRadius: 10,
  },
  viewText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  empty: { alignItems: 'center', paddingTop: 60 },
  emptyText: { color: '#94a3b8', fontSize: 14, marginTop: 12 },
});
