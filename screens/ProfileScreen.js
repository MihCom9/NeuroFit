import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  TextInput,
  View,
  StyleSheet,
  Alert,
  Text,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Button } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'http://172.20.10.3:8080/chat'; 

const ProfileScreen = () => {
  const [profile, setProfile] = useState({
    name: '',
    yearsOld: '',
    weight: '',
    height: '',
    job: '',
    hoursPerDay: '',
    timesPerWeek: '',
  });

  const [aiResponse, setAiResponse] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const saved = await AsyncStorage.getItem('profile');
      if (saved) setProfile(JSON.parse(saved));
    } catch (e) {
      console.error('Load error:', e);
    }
  };

  const saveProfile = async () => {
    try {
      await AsyncStorage.setItem('profile', JSON.stringify(profile));
      Alert.alert('Success', 'Your profile has been saved.');
    } catch (e) {
      console.error('Save error:', e);
    }
  };

  const deleteProfile = async () => {
    try {
      await AsyncStorage.removeItem('profile');
      setProfile({
        name: '',
        yearsOld: '',
        weight: '',
        height: '',
        job: '',
        hoursPerDay: '',
        timesPerWeek: '',
      });
      setAiResponse('');
      Alert.alert('Deleted', 'Your profile has been deleted.');
    } catch (e) {
      console.error('Delete error:', e);
    }
  };

  const sendToAI = async () => {
    const message = `
Act as a fitness trainer and health expert. Based on this user's profile, create a personalized weekly program (Monday to Sunday) with detailed guidance, including rest days. Keep it around 200–300 words:

- Name: ${profile.name}
- Age: ${profile.yearsOld}
- Weight: ${profile.weight} kg
- Height: ${profile.height} cm
- Job: ${profile.job}
- Daily work hours: ${profile.hoursPerDay}
- Weekly workout frequency: ${profile.timesPerWeek}

Give advice that's motivating and clear,no yapping.
`;

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();

      if (data?.reply) {
        setAiResponse(data.reply);
      } else {
        setAiResponse('No response from AI.');
      }
    } catch (e) {
      console.error('AI error:', e);
      setAiResponse('Failed to connect to server. Make sure your IP is correct and server is running.');
    }
  };

  const handleChange = (key, val) => {
    setProfile({ ...profile, [key]: val });
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView>
          <Text style={styles.header}>Set up your information</Text>

          {[
            { key: 'name', placeholder: 'Name', keyboardType: 'default' },
            { key: 'yearsOld', placeholder: 'Age', keyboardType: 'numeric' },
            { key: 'weight', placeholder: 'Weight (kg)', keyboardType: 'numeric' },
            { key: 'height', placeholder: 'Height (cm)', keyboardType: 'numeric' },
            { key: 'job', placeholder: 'Job', keyboardType: 'default' },
            { key: 'hoursPerDay', placeholder: 'Work hours', keyboardType: 'numeric' },
            { key: 'timesPerWeek', placeholder: 'How much days do you want to train', keyboardType: 'numeric' },
          ].map(({ key, placeholder, keyboardType }) => (
            <TextInput
              key={key}
              style={styles.input}
              placeholder={placeholder}
              value={profile[key]}
              onChangeText={(text) => handleChange(key, text)}
              keyboardType={keyboardType}
            />
          ))}

          <Button mode="contained" onPress={saveProfile} style={styles.btn1}>
            Save Profile
          </Button>
          <Button mode="contained" onPress={deleteProfile} style={styles.btn}>
            Delete Profile
          </Button>
          <Button mode="contained" onPress={sendToAI} style={styles.btn1}>
            Ask AI for Advice
          </Button>

          {aiResponse ? (
            <View style={styles.responseBox}>
              <Text style={styles.responseTitle}>AI Response:</Text>
              <Text>{aiResponse}</Text>
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20,width:'90%',marginLeft:20 },
  header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  input: {
    borderWidth: 1,
    borderColor: '#aaa',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    width: '100%',
    backgroundColor:'#fff'
  },
  btn1: { marginVertical: 6 ,backgroundColor: '#007bff'},
  btn: {  marginVertical: 6,color:"white",backgroundColor: '#00bfff'},

  responseBox: {
    marginTop: 20,
    padding: 15,
    borderRadius: 10,
    backgroundColor: '#eef',
  },
  responseTitle: {
    fontWeight: 'bold',
    marginBottom: 5,
  },
});

export default ProfileScreen;
