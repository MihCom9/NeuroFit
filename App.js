import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack'; 
import { Ionicons } from '@expo/vector-icons';

import SmartGadgetScreen from './screens/SmartGadget';
import ExerciseDetailScreen from './screens/ExerciseScreen';
import HomeScreen from './screens/HomeScreen'; 
import ProfileScreen from './screens/ProfileScreen'; 

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const ExerciseStack = () => (
  <Stack.Navigator>
    <Stack.Screen 
      name="SmartGadget" 
      component={SmartGadgetScreen} 
      options={{ headerShown: false }} 
    />
    <Stack.Screen 
      name="ExerciseDetail" 
      component={ExerciseDetailScreen} 
      options={{ headerShown: false }} 
    />
  </Stack.Navigator>
);

const App = () => {
  return (
    <NavigationContainer>
      <Tab.Navigator
        initialRouteName="Home" 
        screenOptions={({ route }) => ({
          tabBarIcon: ({ color, size }) => {
            let iconName;

            if (route.name === 'SmartGadget') {
              iconName = 'fitness'; 
            } else if (route.name === 'Home') {
              iconName = 'home';
            } else if (route.name === 'Profile') {
              iconName = 'person';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
        })}
        tabBarOptions={{
          activeTintColor: 'tomato',
          inactiveTintColor: 'gray',
        }}
      >
        
    
        <Tab.Screen name="Home" component={HomeScreen} />
        <Tab.Screen name="SmartGadget" component={ExerciseStack} />
        <Tab.Screen name="Profile" component={ProfileScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default App;
