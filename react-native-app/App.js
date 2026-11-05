import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import PoolScreen from './src/screens/PoolScreen';
import CaseDetailScreen from './src/screens/CaseDetailScreen';
import WalletScreen from './src/screens/WalletScreen';
import SatisfactionScreen from './src/screens/SatisfactionScreen';

const Stack = createNativeStackNavigator();

export const AppContext = React.createContext({
  server: 'http://188.212.96.235:8085',
  user: null,
  setUser: () => {},
});

export default function App() {
  const [user, setUser] = useState(null);
  const server = 'http://188.212.96.235:8085';

  return (
    <SafeAreaProvider>
      <AppContext.Provider value={{ server, user, setUser }}>
        <NavigationContainer>
          <StatusBar style="light" />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen name="Pool" component={PoolScreen} />
            <Stack.Screen name="CaseDetail" component={CaseDetailScreen} />
            <Stack.Screen name="Wallet" component={WalletScreen} />
            <Stack.Screen name="Satisfaction" component={SatisfactionScreen} />
          </Stack.Navigator>
        </NavigationContainer>
      </AppContext.Provider>
    </SafeAreaProvider>
  );
}
